# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
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
from invenio_records_resources.services.uow import RecordCommitOp, TaskOp
from invenio_requests.tasks import request_moderation
from invenio_users_resources.proxies import current_users_service
from invenio_users_resources.records.api import UserAggregate
from invenio_users_resources.services.users.tasks import execute_moderation_actions
from werkzeug.utils import cached_property

from .errors import UserBlockedException
from .proxies import current_scores


# TODO: This should be moved to invenio-db or invenio-records-resources
class ExceptionOp(Operation):
    """Operation to perform cleanup logic for exceptions.

    This unit of work operation is initialied using another regular operation and maps
    the following methods to the associated "clean-up" unit of work lifecycle methods:

    - ``on_exception``: ``on_register``
    - ``on_rollback``: ``on_commit``
    - ``on_post_rollback``: ``on_post_commit``

    Additionally, it allows to specify an action function to be executed during the
    unit of work lifecycle if an exception is raised. This is to allow rolling back
    any transactions up to the point of the exception, while still performing some
    cleanup logic.
    """

    def __init__(self, commit_op, action_func=None):
        """Initialize exception operation."""
        self.action_func = action_func
        self.commit_op = commit_op

    def on_exception(self, uow, exception):
        """Perform action function if exception is raised."""
        if self.action_func:
            self.action_func(uow, exception)
        self.commit_op.on_register(uow)

    def on_rollback(self, uow):
        """Perform the commit operation on rollback."""
        self.commit_op.on_commit(uow)

    def on_post_rollback(self, uow):
        """Perform the post commit operation on post rollback."""
        self.commit_op.on_post_commit(uow)


class BaseScoreHandler:
    """Base handler to calculate moderation scores based on rules."""

    def __init__(self, rules=None):
        """Initialize the score handler with a set of rules."""
        self._rules = rules

    @cached_property
    def rules(self):
        """Get scoring rules."""
        if isinstance(self._rules, str):
            return current_app.config[self._rules]
        return self._rules or []

    def run(self, identity, draft=None, record=None, uow=None):
        """Calculate the moderation score for a given record or draft."""
        try:
            user = User.query.get(identity.id)
            score = 0
            for rule in self.rules:
                score += rule(identity, draft=draft, record=record)

            apply_actions = current_app.config.get("MODERATION_APPLY_ACTIONS", False)
            user = UserAggregate.get_record(identity.id)
            action_ctx = {
                "user_id": user.id,
                "record_pid": record.pid.pid_value,
                "score": score,
            }
            if score > current_scores.spam_threshold:
                action_ctx["action"] = "block"
                if apply_actions:
                    uow.register(
                        ExceptionOp(
                            RecordCommitOp(
                                user,
                                indexer=current_users_service.indexer,
                                index_refresh=True,
                            ),
                            action_func=lambda *_: user.block(),
                        )
                    )
                    uow.register(
                        ExceptionOp(
                            TaskOp(
                                execute_moderation_actions,
                                user_id=identity.id,
                                action="block",
                            )
                        )
                    )

                    raise UserBlockedException()
                else:
                    current_app.logger.error(
                        "Block moderation action triggered",
                        extra=action_ctx,
                    )
            elif score < current_scores.ham_threshold:
                # If the user is already verified, we don't need to verify again
                if user.verified:
                    return

                action_ctx["action"] = "verify"
                if apply_actions:
                    uow.register(
                        ExceptionOp(
                            RecordCommitOp(
                                user,
                                indexer=current_users_service.indexer,
                                index_refresh=True,
                            ),
                            action_func=lambda *_: user.verify(),
                        )
                    )
                    uow.register(
                        ExceptionOp(
                            TaskOp(
                                execute_moderation_actions,
                                user_id=identity.id,
                                action="approve",
                            )
                        )
                    )
                else:
                    current_app.logger.error(
                        "Verify moderation action triggered",
                        extra=action_ctx,
                    )
            else:
                action_ctx["action"] = "moderate"
                if apply_actions:
                    uow.register(TaskOp(request_moderation, user_id=identity.id))
                else:
                    current_app.logger.error(
                        "Manual moderation action triggered",
                        extra=action_ctx,
                    )
        except Exception:
            current_app.logger.exception("Error calculating moderation score")


class RecordScoreHandler(BaseHandler, BaseScoreHandler):
    """Handler for calculating scores for records."""

    def __init__(self):
        """Initialize with record moderation rules."""
        super().__init__(rules="MODERATION_RECORD_SCORE_RULES")

    def publish(self, identity, draft=None, record=None, uow=None, **kwargs):
        """Calculate and log the score when a record is published."""
        self.run(identity, record=record, uow=uow)


class CommunityScoreHandler(community_moderation.BaseHandler, BaseScoreHandler):
    """Handler for calculating scores for communities."""

    def __init__(self):
        """Initialize with community moderation rules."""
        super().__init__(rules="MODERATION_COMMUNITY_SCORE_RULES")

    def update(self, identity, record=None, data=None, uow=None, **kwargs):
        """Calculate and log the score when a community is updated."""
        self.run(identity, record=record, uow=uow)

    def create(self, identity, record=None, data=None, uow=None, **kwargs):
        """Calculate and log the score when a community is created."""
        self.run(identity, record=record, uow=uow)
