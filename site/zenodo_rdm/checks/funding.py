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
from invenio_checks.models import CheckConfig
from invenio_communities.proxies import current_communities
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.checks.requests import CommunityInclusion, CommunitySubmission
from invenio_records_resources.proxies import current_service_registry
from invenio_requests.proxies import current_requests_service
from invenio_search.api import dsl

from zenodo_rdm.orcha.utils import run_funding_relevance_workflow


class FundingCheck(Check):
    """Check for a match between the record's metadata and the award description."""

    id = "funding"
    title = "Funding check"
    description = "Validates record funding metadata against configured rules."
    sort_order = 30
    sync = False
    target_type = "record"
    hide_parent_checks = True

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

    def _get_input_hash(self, metadata, award_descriptions):
        """Return a hash of the input used to detect when to rerun check."""
        input_data = {
            **metadata,
            "award_description": award_descriptions,
        }
        return hashlib.sha256(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()

    def _get_awards_description(self, record, community):
        """Extract award descriptions from community or record funding metadata."""
        all_funding = list(community["metadata"].get("funding", []))
        if not all_funding:
            all_funding.extend(record.metadata.get("funding", []))

        awards = []
        awards_service = current_service_registry.get("awards")
        for f in all_funding:
            if f["funder"].get("id") == "00k4n6c32":
                if award_id := f.get("award", {}).get("id"):
                    try:
                        award = awards_service.record_cls.pid.resolve(award_id)
                        awards.append(award)
                    except PIDDoesNotExistError:
                        pass

        return [
            description for award in awards
            if (description := award.get("description", {}).get("en")) is not None
        ]

    def _get_ec_requests(self, record, community):
        """Return EC existing open or accepted requests.

        Only queries the community inclusion or community submission requests, open or accepted,
        where the topic matches the record and the receiver is the EOR repository.
        """
        return current_requests_service.search(
            system_identity,
            extra_filter=dsl.Q(
                "bool",
                must=[
                    dsl.Q("term", **{"topic.record": record.pid.pid_value}),
                    dsl.Q("term", **{"receiver.community": community.pid.pid_value}),
                    dsl.Q("terms", **{"type": [CommunitySubmission.type_id, CommunityInclusion.type_id]}),
                    dsl.Q("bool", should=[
                        dsl.Q("term", **{"is_open": True}),
                        dsl.Q("term", **{"status": "accepted"}),
                    ], minimum_should_match=1),
                ],
            ),
        )

    def should_rerun(self, record, config, previous_run, **kwargs):
        """Return True if the check should run again.

        For the funding check, return True if the hash of the inputs (record title and
        description, as well as the award description) has changed since the last check
        run. Otherwise, return False as the last run can be reused.

        A pending or running run keeps the last completed hash, so an unrelated edit
        waits for it instead of starting a second run.
        """
        community = current_communities.service.record_cls.get_record(config.community_id)
        awards = self._get_awards_description(record, community)

        metadata = record["metadata"]
        check_metadata = {
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
        }

        input_hash = self._get_input_hash(check_metadata, awards)
        return previous_run.state.get("input_hash") != input_hash

    def run(self, record, config: CheckConfig, **kwargs):
        """Run the funding relevance check on a record with the given configuration."""
        def get_updated_result(check_result, message, success):
            check_result.success = success
            check_result.description = message
            if not success:
                check_result.errors.append(
                    {
                        "field": "metadata.funding",
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
        award_descriptions = self._get_awards_description(record, community)

        is_ec_community = community.slug == "eu"
        no_ec_requests = self._get_ec_requests(record, community).total == 0
        if is_ec_community and no_ec_requests:
            return get_updated_result(
                check_result,
                message="Skipping EOR funding check run, as there is no open request to the community.",
                success=False,
            ), {}

        metadata = record["metadata"]
        check_metadata = {
            "title": metadata.get("title", ""),
            "description": metadata.get("description", ""),
        }
        input_hash = self._get_input_hash(check_metadata, award_descriptions)

        if not award_descriptions:
            return get_updated_result(
                check_result,
                message="No award found for the project or record.",
                success=False,
            ), {"input_hash": input_hash}
        if len(award_descriptions) > 1:
            return get_updated_result(
                check_result,
                message="Multiple awards found for the project or record. The check will be skipped.",
                success=False,
            ), {"input_hash": input_hash}

        try:
            response = run_funding_relevance_workflow(check_metadata, award_descriptions[0])

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
