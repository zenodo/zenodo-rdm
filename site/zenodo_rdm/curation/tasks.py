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
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_search.engine import dsl

from zenodo_rdm.curation.curators import EURecordCurator


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
    created_before = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    updated_after = (datetime.fromisoformat(since) - timedelta(hours=12)).isoformat()

    query = dsl.Q(
        "bool",
        must=[
            dsl.Q("term", **{"metadata.funding.funder.id": "00k4n6c32"}),
            dsl.Q("term", **{"is_deleted": False}),
            dsl.Q(
                "range",
                created={
                    "lte": created_before,
                },
            ),
            dsl.Q(
                "range",
                updated={
                    "gte": updated_after,
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
            )
        ],
    )
    search = records_service.create_search(
        system_identity,
        records_service.record_cls,
        records_service.config.search,
        extra_filter=query,
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

    current_app.logger.error(
        "EU curation processed",
        extra=ctx,
    )
