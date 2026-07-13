# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo-specific record checks."""
import time

from invenio_access.permissions import system_identity
from invenio_checks.base import (
    Check,  # Import CheckResult when subcommunity checks are integrated
)
from invenio_checks.contrib.file_formats import (
    CheckResult,  # Remove when subcommunity checks are integrated
)
from invenio_checks.models import CheckConfig
from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry


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

    def _get_award_description(self, funding):
        """Extract award short description from community funding metadata."""
        if not funding:
            return None

        award_id = (funding[0].get("award") or {}).get("id")
        if not award_id:
            return None

        awards_service = current_service_registry.get("awards")
        award = awards_service.read(system_identity, award_id)

        return (
            award.to_dict()
            .get("short_description", {})
            .get("en")
        )

    def run(self, record, config: CheckConfig):
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
        print("check_result title", params.get("funding_title", self.default_messages["title"]))
        result = CheckResult(
            id=self.id,
            title=params.get("funding_title", self.default_messages["title"]),
            # NOTE: We default to the default description for now, while the check is running/pending
            description=description,
        )

        community = current_communities.service.record_cls.get_record(config.community_id)
        community_funding = community["metadata"].get("funding") or []
        award_description = self._get_award_description(community_funding)

        if not award_description:
            return get_updated_result(
                result,
                message="No award found for the project.",
                success=False,
            )

        try:
            client = _orcha_client()
            token = _workflow_token(client)

            INSTRUCTIONS = """
                Given a record's title and description, and an EU grant's official description,
                determine whether the record is plausibly related to the grant.
    
                A record matches if it shares the same research domain, methodology,
                or outputs as the grant.
    
                Return:
                - match: True if the record is plausibly related to the grant, False otherwise
                - message: a one-sentence explanation of your decision
            """

            metadata = record["metadata"]
            response = client.trigger_workflow(
                payload={
                    "workflow_type": "check_funding_relevance",
                    "params": {
                        "metadata": {
                            "title": metadata.get("title", ""),
                            "description": metadata.get("description", ""),
                        },
                        "award_description": award_description,
                        "rule": INSTRUCTIONS,
                    },
                },
                token=token,
            )
            workflow_id = response["public_id"]
            # poll for result using a scoped token
            workflow_token = _workflow_token(client, workflow_id)
            # Poll until done
            response = {}
            for _ in range(20):
                time.sleep(3)
                data = client.get_workflow(workflow_id, workflow_token)
                if data["status"] in ("success", "error"):
                    response = data.get("result") or {}
                    break

        except Exception:
            return get_updated_result(
                result,
                message="Funding validation service unavailable.",
                success=False,
            )

        match = response.get("match")
        if match is not None:
            return get_updated_result(result, response.get("message"), match)
        return get_updated_result(
            result,
            message="Funding validation service timed out, please try again.",
            success=False,
        )
