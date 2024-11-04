# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Handlers for ZenodoRDM Moderation."""

import invenio_rdm_records.services.communities.moderation as community_moderation
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_accounts.models import User
from invenio_db.uow import Operation
from invenio_rdm_records.services.components.verified import BaseHandler
from invenio_users_resources.records.api import UserAggregate
from invenio_users_resources.proxies import current_users_service
from invenio_users_resources.services.users.tasks import execute_moderation_actions
from invenio_records_resources.services.uow import TaskOp, RecordCommitOp
from invenio_requests.tasks import request_moderation


from .proxies import current_scores


class ExceptionOp(Operation):
    def __init__(self, commit_op, action_func=None):
        self.action_func = action_func
        self.commit_op = commit_op

    def on_exception(self, uow, exception):
        if self.action_func:
            self.action_func(uow, exception)
        self.commit_op.on_register(uow)

    def on_rollback(self, uow):
        self.commit_op.on_commit()

    def on_post_rollback(self, uow):
        self.commit_op.on_post_commit()


class BaseScoreHandler:
    """Base handler to calculate moderation scores based on rules."""

    def __init__(self, rules=None):
        """Initialize the score handler with a set of rules."""
        self.rules = rules

    def run(self, identity, draft=None, record=None, user=None, uow=None):
        """Calculate the moderation score for a given record or draft."""
        score = 0
        rules = current_app.config[self.rules]
        for rule in rules:
            score += rule(identity, draft=draft, record=record)

        apply_actions = current_app.config.get("MODERATION_APPLY_ACTIONS", False)
        if score > current_scores.spam_threshold:
            if apply_actions:
                uow.register(
                    ExceptionOp(
                        RecordCommitOp(user, indexer=current_users_service.indexer, index_refresh=True),
                        action_func=lambda *_: user.block(),
                    )
                )
                uow.register(
                    ExceptionOp(TaskOp(execute_moderation_actions, user_id=identity.id, action="block"))
                )
            else:
                current_app.logger.warning(
                    "Moderation action triggered",
                    extra={
                        "action": "block_user",
                        "record_pid": record.id,
                        "score": score,
                    },
                )
        elif score < current_scores.ham_threshold:
            if apply_actions:
                uow.register(
                    ExceptionOp(
                        RecordCommitOp(user, indexer=current_users_service.indexer, index_refresh=True),
                        action_func=lambda *_: user.verify(),
                    )
                )
                uow.register(
                    ExceptionOp(TaskOp(execute_moderation_actions, user_id=identity.id, action="approve"))
                )
            else:
                current_app.logger.warning(
                    "Moderation action triggered",
                    extra={
                        "action": "verify_user",
                        "record_pid": record.id,
                        "score": score,
                    },
                )
        else:
            if apply_actions:
                uow.register(TaskOp(request_moderation, user_id=identity.id))
            else:
                current_app.logger.warning(
                    "Moderation action triggered",
                    extra={
                        "action": "moderate_user",
                        "record_pid": record.id,
                        "score": score,
                    },
                )


class RecordScoreHandler(BaseHandler, BaseScoreHandler):
    """Handler for calculating scores for records."""

    def __init__(self):
        """Initialize with record moderation rules."""
        super().__init__(rules="RDM_RECORD_MODERATION_SCORE_RULES")

    def publish(self, identity, draft=None, record=None, uow=None):
        """Calculate and log the score when a record is published."""
        score = self.run(identity, record=record, uow=uow)
        current_app.logger.warning(
            "Record published with moderation score",
            extra={"record_pid": record.id, "score": score},
        )


class CommunityScoreHandler(community_moderation.BaseHandler, BaseScoreHandler):
    """Handler for calculating scores for communities."""

    def __init__(self):
        """Initialize with community moderation rules."""
        super().__init__(rules="COMMUNITY_MODERATION_SCORE_RULES")

    def update(self, identity, record=None, data=None, uow=None):
        """Calculate and log the score when a community is updated."""
        score = self.run(identity, record=record, uow=uow)
        current_app.logger.info(
            f"Community {record.metadata['title']} updated with moderation score: {score}"
        )

    def create(self, identity, record=None, data=None, uow=None):
        """Calculate and log the score when a community is created."""
        score = self.run(identity, record=record, uow=uow)
        current_app.logger.info(
            f"Community {record.metadata['title']} created with moderation score: {score}"
        )
