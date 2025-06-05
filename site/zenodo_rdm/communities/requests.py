# -*- coding: utf-8 -*-
#
# Copyright (C) 202% CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Communities requests."""

from datetime import datetime

from invenio_checks.api import CheckRunAPI
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_rdm_records.requests import (
    community_inclusion,
    community_submission,
)
from invenio_records_resources.services.uow import ModelCommitOp
from invenio_requests.customizations import actions


class SubmissionSubmitAction(actions.SubmitAction):
    """Submit action."""

    def execute(self, identity, uow):
        """Execute the submit action."""
        draft = self.request.topic.resolve()
        service._validate_draft(identity, draft)
        # Set the record's title as the request title.
        self.request["title"] = draft.metadata["title"]

        # Run checks on record or draft
        if record.has_draft:
            draft = service.draft_cls.pid.resolve(
                record.pid.pid_value, registered_only=False
            )
            # Use the draft for checks
            record = draft

        # Run checks
        CheckRunAPI.run_checks(
            identity=identity,
            record=record,
        )

        super().execute(identity, uow)

class SubmissionCreateAction(actions.CreateAction):
    """Create action."""

    def execute(self, identity, uow):
        """Execute the create action."""
        draft = self.request.topic.resolve()
        # Run checks
        CheckRunAPI.run_checks(
            identity=identity,
            record=record,
        )
        super().execute(identity, uow)


class CommunitySubmission(community_submission.CommunitySubmission):
    """Request to add a subcommunity to a Zenodo community."""

    available_actions = {
        "create": SubmissionCreateAction,
        "submit": SubmissionSubmitAction,
        "delete": actions.DeleteAction,
        "accept": community_submission.AcceptAction,
        "decline": community_submission.DeclineAction,
        "cancel": community_submission.CancelAction,
        "expire": community_submission.ExpireAction,
    }


class InclusionSubmitAction(actions.SubmitAction):
    """Submit action."""

    def execute(self, identity, uow):
        """Execute the submit action."""
        record = self.request.topic.resolve()
        # Set the record's title as the request title.
        self.request["title"] = record.metadata["title"]

        # Run checks on record or draft
        if record.has_draft:
            draft = service.draft_cls.pid.resolve(
                record.pid.pid_value, registered_only=False
            )
            # Use the draft for checks
            record = draft

        # Run checks
        CheckRunAPI.run_checks(
            identity=identity,
            record=record,
        )

        super().execute(identity, uow)


class CommunityInclusion(community_inclusion.CommunityInclusion):
    """Request for a published record to be included in a community."""

    available_actions = {
        "create": actions.CreateAction,
        "submit": InclusionSubmitAction,
        "delete": actions.DeleteAction,
        "accept": community_inclusion.AcceptAction,
        "decline": actions.DeclineAction,
        "cancel": actions.CancelAction,
        "expire": actions.ExpireAction,
    }
