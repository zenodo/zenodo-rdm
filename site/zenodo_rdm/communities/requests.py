# -*- coding: utf-8 -*-
#
# Copyright (C) 202% CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Communities requests."""

from datetime import datetime

from invenio_checks.models import CheckConfig, CheckRun, CheckRunStatus
from invenio_checks.proxies import current_checks_registry
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

        # TODO: Run checks on record or draft

        super().execute(identity, uow)


class CommunitySubmission(community_submission.CommunitySubmission):
    """Request to add a subcommunity to a Zenodo community."""

    available_actions = {
        "create": actions.CreateAction,
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

        # FIXME: This has been copied from the checks component
        community_ids = set()
        community = self.request.receiver.resolve()
        community_ids.add(str(community.id))
        if community.parent:
            community_ids.add(str(community.parent.id))

        checks = CheckConfig.query.filter(
            CheckConfig.community_id.in_(community_ids)
        ).all()

        for check in checks:
            try:
                check_cls = current_checks_registry.get(check.check_id)
                start_time = datetime.utcnow()
                res = check_cls().run(record, check)
                if not res.sync:
                    continue

                latest_check = (
                    CheckRun.query.filter(
                        CheckRun.config_id == check.id,
                        CheckRun.record_id == record.id,
                    )
                    # We prefer the latest non-draft check
                    .order_by(CheckRun.is_draft.desc())
                    .first()
                )

                if not latest_check:
                    latest_check = CheckRun(
                        config_id=check.id,
                        record_id=record.id,
                        is_draft=record.is_draft,
                        revision_id=record.revision_id,
                        start_time=start_time,
                        end_time=datetime.utcnow(),
                        status=CheckRunStatus.COMPLETED,
                        state="",
                        result=res.to_dict(),
                    )
                else:
                    latest_check.is_draft = record.is_draft
                    latest_check.revision_id = record.revision_id
                    latest_check.start_time = start_time
                    latest_check.end_time = datetime.utcnow()
                    latest_check.result = res.to_dict()

                # Create/update the check run to the database
                uow.register(ModelCommitOp(latest_check))
            except Exception:
                continue

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
