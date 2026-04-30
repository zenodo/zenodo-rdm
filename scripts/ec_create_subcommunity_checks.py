# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Script to create metadata checks for the EC community and sub-communities.

Usage:

.. code-block:: shell

    invenio shell ec_create_subcommunity_checks.py
"""

from copy import deepcopy

from invenio_checks.api import ChecksAPI
from invenio_checks.models import CheckConfig, Severity
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_records_resources.services.uow import UnitOfWork
from invenio_requests.records.api import Request
from invenio_requests.records.models import RequestMetadata
from werkzeug.local import LocalProxy

community_service = LocalProxy(lambda: current_communities.service)


MEMBER_RULES = {
    "target_type": "community",
}

VALIDATION_RULES = {
    "target_type": "community",
}

RECORD_METADATA_RULES = {
    "sync": False,
    "target_type": "community",
}

METADATA_RULES = {
    "target_type": "community",
    "rules": [
        {
            "id": "metadata:title",
            "title": "Name",
            "message": "Name",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.title"},
                    "operator": "!=",
                    "right": None,
                }
            ],
        },
        {
            "id": "slug",
            "title": "Identifier",
            "message": "Identifier",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "slug"},
                    "operator": "!=",
                    "right": None,
                }
            ],
        },
        {
            "id": "metadata:type",
            "title": "Type",
            "message": "Type",
            "description": "The community type should be Project.",
            "level": "error",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.type.id"},
                    "operator": "==",
                    "right": "project",
                }
            ],
        },
        {
            "id": "metadata:description",
            "title": "Short description",
            "message": "Short description",
            "level": "warning",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.description"},
                    "operator": "!=",
                    "right": None,
                }
            ],
        },
        {
            "id": "metadata:website",
            "title": "Website",
            "message": "Website",
            "level": "info",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "metadata.website"},
                    "operator": "!=",
                    "right": None,
                }
            ],
        },
        {
            "id": "metadata:logo",
            "title": "Logo",
            "message": "Logo",
            "description": "The community should have a logo.",
            "level": "info",
            "checks": [
                {
                    "type": "comparison",
                    "left": {"type": "field", "path": "files.entries.logo"},
                    "operator": "!=",
                    "right": None,
                }
            ],
        },
        # TODO: implement organization checks
    ]
}


def create_eu_subcommunity_checks():
    eu_comm = community_service.record_cls.pid.resolve("eu")
    create_member_checks(eu_comm)
    create_project_validation_checks(eu_comm)
    create_record_metadata_checks(eu_comm)
    create_metadata_checks(eu_comm)
    print("EU Open Research Repository subcommunity checks created/updated successfully.")
    run_checks_for_existing_requests(eu_comm)


def run_checks_for_existing_requests(eu_comm):
    configs = ChecksAPI.get_configs([eu_comm.id], "community")
    if not configs:
        print("No subcommunity check configs found, skipping.")
        return

    # Subcommunity requests
    open_request_models = RequestMetadata.query.filter(
        RequestMetadata.json.op('->>')('type') == "subcommunity",
        RequestMetadata.json.op('->>')('status') == "submitted",
    ).all()

    for req_model in open_request_models:
        request = Request.get_record(req_model.id)

        # Only process requests where receiver is the EU community
        try:
            receiver = request.receiver.resolve()
        except Exception:
            continue
        if str(receiver.id) != str(eu_comm.id):
            continue

        subcommunity = request.topic.resolve()

        with UnitOfWork(db.session) as uow:
            for config in configs:
                ChecksAPI.run_check(config, subcommunity, uow)
            uow.commit()

    print("Done running checks for existing subcommunity requests.")


def create_member_checks(eu_comm):
    existing_check = CheckConfig.query.filter(
        CheckConfig.community_id == eu_comm.id,
        CheckConfig.check_id == "subcommunity_member",
        CheckConfig.params["target_type"].as_string() == "community"
    ).one_or_none()
    if existing_check:
        existing_check.params = MEMBER_RULES
    else:
        check_config = CheckConfig(
            community_id=eu_comm.id,
            check_id="subcommunity_member",
            params=MEMBER_RULES,
            severity=Severity.FAIL,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(
        f"Subcommunity member affiliation checks created/updated successfully for community {eu_comm.slug}."
    )


def create_project_validation_checks(eu_comm):
    existing_check = CheckConfig.query.filter(
        CheckConfig.community_id == eu_comm.id,
        CheckConfig.check_id == "subcommunity_validation",
        CheckConfig.params["target_type"].as_string() == "community"
    ).one_or_none()
    if existing_check:
        existing_check.params = VALIDATION_RULES
    else:
        check_config = CheckConfig(
            community_id=eu_comm.id,
            check_id="subcommunity_validation",
            params=VALIDATION_RULES,
            severity=Severity.FAIL,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(
        f"Subcommunity project validation checks created/updated successfully for community {eu_comm.slug}."
    )


def create_record_metadata_checks(eu_comm):
    existing_check = CheckConfig.query.filter(
        CheckConfig.community_id == eu_comm.id,
        CheckConfig.check_id == "subcommunity_record_metadata",
        CheckConfig.params["target_type"].as_string() == "community"
    ).one_or_none()
    if existing_check:
        existing_check.params = RECORD_METADATA_RULES
        existing_check.severity = Severity.FAIL
    else:
        check_config = CheckConfig(
            community_id=eu_comm.id,
            check_id="subcommunity_record_metadata",
            params=RECORD_METADATA_RULES,
            severity=Severity.WARN,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(
        f"Subcommunity funding metadata checks created/updated successfully for community {eu_comm.slug}."
    )


def create_metadata_checks(eu_comm):
    check_config_params = deepcopy(METADATA_RULES)
    check_message = "To comply with Horizon Europe's open science requirements, the community should provide the project's __FIELD__."
    for rule in check_config_params["rules"]:
        if 'description' not in rule:
            rule["description"] = check_message.replace("__FIELD__", rule["message"].lower())

    existing_check = CheckConfig.query.filter(
        CheckConfig.community_id == eu_comm.id,
        CheckConfig.check_id == "subcommunity_metadata",
        CheckConfig.params["target_type"].as_string() == "community"
    ).one_or_none()
    if existing_check:
        existing_check.params = check_config_params
    else:
        check_config = CheckConfig(
            community_id=eu_comm.id,
            check_id="subcommunity_metadata",
            params=check_config_params,
            severity=Severity.INFO,
            enabled=True,
        )
        db.session.add(check_config)
    db.session.commit()
    print(
        f"Subcommunity metadata checks created/updated successfully for community {eu_comm.slug}."
    )


if __name__ == "__main__":
    create_eu_subcommunity_checks()
