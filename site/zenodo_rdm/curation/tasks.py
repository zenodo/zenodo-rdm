# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Tasks for curation."""

from datetime import datetime, timedelta, timezone

from celery import shared_task
from flask import current_app
from flask_mail import Message
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_search.engine import dsl

from zenodo_rdm.curation.curators import EURecordCurator

RESULT_EMAIL_BODY = """
EU Record Curation Processed

Finished at: {finished_at}
Processed since: {since}
Total Records Processed: {processed}
Records Failed: {failed}
Records Approved: {approved}
Record IDs Approved:
{records_moved}
"""


def _send_result_email(content):
    """Send curation result as email."""
    subject = f"EU Record Curation Processed {datetime.now().date()}"
    body = RESULT_EMAIL_BODY.format(finished_at=datetime.now(timezone.utc), **content)
    sender = current_app.config["MAIL_DEFAULT_SENDER"]
    admin_email = current_app.config["APP_RDM_ADMIN_EMAIL_RECIPIENT"]
    recipients = admin_email
    if not isinstance(admin_email, list):
        recipients = [admin_email]
    mail_ext = current_app.extensions["mail"]
    msg = Message(subject, sender=sender, recipients=recipients, body=body)
    mail_ext.send(msg)


def _get_eu_records_query(since):
    """Get dsl query for records to be processed."""
    created_before = datetime.now(timezone.utc) - timedelta(days=30)
    updated_after = datetime.fromisoformat(since) - timedelta(hours=12)

    # Get records with EC funding and not in EU community already and not created in last 30 days
    ec_funded = dsl.Q(
        "bool",
        must=[
            dsl.Q("term", **{"metadata.funding.funder.id": "00k4n6c32"}),
            dsl.Q("term", **{"is_deleted": False}),
            dsl.Q(
                "range",
                created={
                    "lte": created_before.isoformat(),
                },
            ),
        ],
        must_not=[
            dsl.Q(
                "term",
                **{
                    "parent.communities.ids": current_app.config.get(
                        "EU_COMMUNITY_UUID"
                    )
                },
            ),
        ],
    )

    updated_after_since = dsl.Q(
        "bool",
        must=[
            dsl.Q(
                "range",
                updated={
                    "gte": updated_after.isoformat(),
                },
            ),
        ],
    )

    # Created 31 days before (with a 6 hour buffer)
    new_created = dsl.Q(
        "bool",
        must=[
            dsl.Q(
                "range",
                created={
                    "gte": (created_before - timedelta(days=1, hours=6)).isoformat(),
                },
            ),
        ],
    )

    return ec_funded & (updated_after_since | new_created)


@shared_task
def run_eu_record_curation(since):
    """Run EC Curator."""
    ctx = {
        "processed": 0,
        "approved": 0,
        "failed": 0,
        "since": since,
        "records_moved": [],
    }
    dry_run = not current_app.config.get("CURATION_ENABLE_EU_CURATOR")
    curator = EURecordCurator(dry=dry_run)

    search = records_service.create_search(
        system_identity,
        records_service.record_cls,
        records_service.config.search,
        extra_filter=_get_eu_records_query(since),
    )

    for item in search.scan():
        record = records_service.record_cls.pid.resolve(item["id"])
        try:
            result = curator.run(record=record)
            ctx["processed"] += 1
            if result["evaluation"]:
                ctx["approved"] += 1
                if not dry_run:
                    ctx["records_moved"].append(record.pid.pid_value)
        except Exception:
            # NOTE Since curator's raise_rules_exc is by default false, rules would not fail.
            # This catches failures due to other reasons
            ctx["failed"] += 1

    if not dry_run:
        _send_result_email(ctx)

    current_app.logger.error(
        "EU curation processed",
        extra=ctx,
    )
