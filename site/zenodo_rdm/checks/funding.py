# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo-specific record checks."""
import hashlib
import json

from invenio_access.permissions import system_identity
from invenio_checks.base import Check, CheckResult
from invenio_checks.models import CheckConfig, CheckRunStatus
from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry

from zenodo_rdm.orcha.utils import run_funding_relevance_workflow


class FundingCheck(Check):
    """Check for a match between the record's metadata and the award description."""

    id = "funding"
    title = "Funding check"
    description = "Validates record funding metadata against configured rules."
    sort_order = 30
    sync = False
    target_type = "record"

    default_messages = {
        "title": "Record metadata should match grant description",
        "description": "The system compares the record title and description against the official EU grant description.",
    }

    def pending_result(self, params):
        """Overwrite initial result dict stored for pending checks."""
        return {
            "id": self.id,
            "title": params.get("funding_title", self.default_messages["title"]),
            "description": params.get("funding_description", self.default_messages["description"]),
        }

    def _get_input_hash(self, metadata, award_description):
        """Return a hash of the input used to detect when to rerun check."""
        input_data = {
            **metadata,
            "award_description": award_description,
        }
        return hashlib.sha256(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()

    def should_rerun(self, record, config, previous_run, **kwargs):
        """Return True if the check should run again.

        For the funding check, return True if the hash of the inputs (record title and
        description, as well as the award description) has changed since the last check
        run. Otherwise, return False as the last run can be reused.
        """
        if not previous_run or previous_run.status != CheckRunStatus.COMPLETED:
            return True

        community = current_communities.service.record_cls.get_record(config.community_id)
        community_funding = community["metadata"].get("funding") or []
        award_description = self._get_award_description(community_funding)

        metadata = record["metadata"]
        check_metadata = {
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
        }

        input_hash = self._get_input_hash(check_metadata, award_description)

        return previous_run.state.get("input_hash") != input_hash

    def _get_award_description(self, funding):
        """Extract award description from community funding metadata."""
        if not funding:
            return None

        award_id = (funding[0].get("award") or {}).get("id")
        if not award_id:
            return None

        awards_service = current_service_registry.get("awards")
        award = awards_service.read(system_identity, award_id)

        return (
            award.to_dict()
            .get("description", {})
            .get("en")
        )

    def run(self, record, config: CheckConfig, **kwargs):
        """Run the funding relevance check on a record with the given configuration."""
        def get_updated_result(check_result, message, success):
            check_result.success = success
            check_result.description = message
            if not success:
                check_result.errors.append(
                    {
                        "field": f"funding",
                        "messages": [message],
                        "description": description,
                        "severity": config.severity.error_value,
                    }
                )
            return check_result

        params = config.params
        description = params.get(
            "funding_description",
            self.default_messages["description"],
        )
        check_result = CheckResult(
            id=self.id,
            title=params.get("funding_title", self.default_messages["title"]),
            # NOTE: We default to the default description for now, while the check is running/pending
            description=description,
        )

        community = current_communities.service.record_cls.get_record(config.community_id)
        community_funding = community["metadata"].get("funding") or []
        award_description = self._get_award_description(community_funding)

        metadata = record["metadata"]
        check_metadata = {
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
        }
        input_hash = self._get_input_hash(check_metadata, award_description)

        if not award_description:
            return get_updated_result(
                check_result,
                message="No award found for the project.",
                success=False,
            ), {"input_hash": input_hash}

        try:
            response = run_funding_relevance_workflow(check_metadata, award_description)

        except Exception:
            return get_updated_result(
                check_result,
                message="Funding validation service unavailable.",
                success=False,
            ), {}

        match = response.get("match")
        if match is not None:
            return get_updated_result(
                check_result, response.get("message"), match
            ), {
                "input_hash": input_hash,
                "workflow_id": response.get("workflow_id")
            }
        return get_updated_result(
            check_result,
            message="Funding validation service timed out, please try again.",
            success=False,
        ), {}
