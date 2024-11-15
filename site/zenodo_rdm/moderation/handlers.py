# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Handlers for ZenodoRDM Moderation.

The handlers are responsible for calculating moderation score based on the
configured rules and afterwards apply moderation actions based on the
calculated scores.

Moderation actions are based on the following logic:

| Status/Decision |  H + H  |    H + S   |    S + S    |
|-----------------|:-------:|:----------:|:-----------:|
| Unverified      | Approve |  Moderate  |    Block    |
| Verified        |   (-)   | (Moderate) | (Moderate)* |

- For the ``Decision`` column, H = Ham, S = Spam. The first value is the score-based
  evaluation, and the second value is based on the spam model prediction.
- ``(...)``: Check is evaluated asynchronously, and not in the handler, since we don't
  want to "delay" the HTTP response to the user.
- ``*``: In the scenario where we "Moderate" a Verified user when both the score
  and the spam model predict spam, if the user's email domain is blocked or moderated,
  we actually block the user. Otherwise we open a moderation request to be reviewed by
  admins manually.
"""

import invenio_rdm_records.services.communities.moderation as community_moderation
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_rdm_records.services.components.verified import BaseHandler
from invenio_records_resources.services.uow import RecordCommitOp, TaskOp
from invenio_users_resources.proxies import current_users_service as users_service
from invenio_users_resources.records.api import UserAggregate
from invenio_users_resources.services.users.tasks import execute_moderation_actions
from werkzeug.utils import cached_property

from .errors import UserBlockedException
from .proxies import current_scores
from .tasks import run_moderation_handlers, update_moderation_request
from .uow import ExceptionOp


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

    @property
    def should_apply_actions(self):
        """Return if moderation actions should be applied."""
        return current_app.config.get("MODERATION_APPLY_ACTIONS", False)

    @cached_property
    def exempt_users(self):
        """Return users exempt from moderation."""
        return set(current_app.config.get("MODERATION_EXEMPT_USERS", []))

    def run(self, identity, draft=None, record=None, user=None, uow=None):
        """Calculate the moderation score for a given record or draft."""
        try:
            if user.id in self.exempt_users:
                current_app.logger.debug(
                    "User is exempt from moderation", extra={"user_id": user.id}
                )
                return

            score = 0
            for rule in self.rules:
                score += rule(identity, draft=draft, record=record)

            action_ctx = {
                "user_id": user.id,
                "record_pid": record.pid.pid_value,
                "score": score,
            }
            current_app.logger.debug("Moderation score calculated", extra=action_ctx)
            if score > current_scores.spam_threshold:
                action_ctx["action"] = "block"
                if self.should_apply_actions:
                    # If user is verified, we need to (re)open the moderation
                    # request to be reviewed by admins manually again
                    if user.verified:
                        action_ctx["action"] = "moderate"
                        self._moderate(user, uow, action_ctx)
                    else:
                        self._block(user, uow, action_ctx)
                else:
                    current_app.logger.error(
                        "Block moderation action triggered",
                        extra=action_ctx,
                    )
            elif score < current_scores.ham_threshold:
                action_ctx["action"] = "approve"

                if user.verified:
                    current_app.logger.debug(
                        "User is verified, skipping moderation actions",
                        extra=action_ctx,
                    )
                    return

                if self.should_apply_actions:
                    self._approve(user, uow, action_ctx)
                else:
                    current_app.logger.error(
                        "Verify moderation action triggered",
                        extra=action_ctx,
                    )
            else:
                action_ctx["action"] = "moderate"
                if self.should_apply_actions:
                    self._moderate(user, uow, action_ctx)
                else:
                    current_app.logger.error(
                        "Manual moderation action triggered",
                        extra=action_ctx,
                    )
        # Re-raise UserBlockedException to prevent further processing of the record
        except UserBlockedException:
            raise
        # Failsafe in the moderation check is faulty
        except Exception:
            current_app.logger.exception("Error calculating moderation score")

    def _moderate(self, user, uow, action_ctx):
        """Perform manual moderation action."""
        uow.register(
            TaskOp(update_moderation_request, user_id=user.id, action_ctx=action_ctx)
        )

    def _approve(self, user, uow, action_ctx):
        """Perform approve action."""
        user.verify()
        uow.register(
            RecordCommitOp(user, indexer=users_service.indexer, index_refresh=True),
        )
        uow.register(
            TaskOp(execute_moderation_actions, action="approve", user_id=user.id)
        )
        uow.register(
            TaskOp(
                update_moderation_request,
                user_id=user.id,
                action_ctx=action_ctx,
            )
        )

    def _block(self, user, uow, action_ctx):
        """Perform block action."""
        uow.register(
            ExceptionOp(
                RecordCommitOp(user, indexer=users_service.indexer, index_refresh=True),
                action_func=lambda *_: user.block(),
            )
        )
        uow.register(
            ExceptionOp(
                TaskOp(execute_moderation_actions, user_id=user.id, action="block")
            )
        )
        uow.register(
            ExceptionOp(
                TaskOp(
                    update_moderation_request,
                    user_id=user.id,
                    action_ctx=action_ctx,
                )
            )
        )

        # We raise an exception to prevent further processing of the record. This also
        # means that the unit of work will rollback the DB transaction, but perform the
        # block action from above.
        raise UserBlockedException()


class RecordScoreHandler(BaseHandler, BaseScoreHandler):
    """Handler for calculating scores for records."""

    def __init__(self):
        """Initialize with record moderation rules."""
        super().__init__(rules="MODERATION_RECORD_SCORE_RULES")

    def publish(self, identity, draft=None, record=None, uow=None, **kwargs):
        """Calculate and log the score when a record is published."""
        user_id = None
        if identity == system_identity:
            user_id = record.parent.access.owned_by.owner_id
        else:
            user_id = identity.id
        if user_id is None:
            current_app.logger.error(
                "No user found for moderation action", stack_info=True
            )
            return
        user = UserAggregate.get_record(user_id)

        # Perform the moderation checks asynchronously for verified users
        if user.verified:
            uow.register(
                TaskOp(
                    run_moderation_handlers,
                    user_id=user.id,
                    record_id=str(record.id),
                )
            )
            return

        self.run(identity, record=record, user=user, uow=uow)


class CommunityScoreHandler(community_moderation.BaseHandler, BaseScoreHandler):
    """Handler for calculating scores for communities."""

    def __init__(self):
        """Initialize with community moderation rules."""
        super().__init__(rules="MODERATION_COMMUNITY_SCORE_RULES")

    def _run(self, identity, record, uow):
        """Run the moderation scoring."""
        # Skip moderation for system actions (e.g. subcommunity inclusion actions)
        if identity == system_identity:
            return
        user = UserAggregate.get_record(identity.id)

        # Perform the moderation checks asynchronously for verified users
        if user.verified:
            uow.register(
                TaskOp(
                    run_moderation_handlers,
                    user_id=user.id,
                    community_id=str(record.id),
                )
            )
            return

        # Otherwise calculate the score synchronously
        self.run(identity, record=record, user=user, uow=uow)

    def update(self, identity, record=None, data=None, uow=None, **kwargs):
        """Calculate and log the score when a community is updated."""
        self._run(identity, record=record, uow=uow)

    def create(self, identity, record=None, data=None, uow=None, **kwargs):
        """Calculate and log the score when a community is created."""
        self._run(identity, record=record, uow=uow)
