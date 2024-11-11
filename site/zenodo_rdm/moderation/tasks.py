# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tasks for moderation."""

from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_db.uow import UnitOfWork
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_records_resources.services.uow import RecordCommitOp
from invenio_requests.customizations.event_types import CommentEventType
from invenio_requests.customizations.user_moderation.user_moderation import (
    UserModerationRequest,
)
from invenio_requests.proxies import current_events_service as events_service
from invenio_requests.proxies import current_requests_service as requests_service
from invenio_requests.proxies import (
    current_user_moderation_service as user_moderation_service,
)
from invenio_requests.records.api import Request
from invenio_requests.services.user_moderation.errors import OpenRequestAlreadyExists
from invenio_search.engine import dsl
from invenio_users_resources.proxies import current_users_service as users_service


@shared_task(ignore_result=True)
def update_moderation_request(user_id, action_ctx):
    """Update a moderation request from an automated moderation action.

    This task is called by moderation handlers to log the results of an
    automated moderation action on the user moderation request. If no request
    exists for the user, a new one is created.
    """
    # Find the moderation request for the user (even if it's closed)
    results = requests_service.search(
        system_identity,
        extra_filter=dsl.query.Bool(
            "must",
            # NOTE: We don't filter by is_open=True, since we also need closed requests
            must=[
                dsl.Q("term", **{"type": UserModerationRequest.type_id}),
                dsl.Q("term", **{"topic.user": user_id}),
            ],
        ),
    )
    request_id = next(results.hits)["id"] if results.total > 0 else None

    # NOTE: We only need the unit of work becase we might need to create a new request
    with UnitOfWork() as uow:
        # If no request exists, create a new one
        if request_id is None:
            try:
                request_id = user_moderation_service.request_moderation(
                    system_identity, user_id=user_id, uow=uow
                ).id
                current_app.logger.debug(
                    "User moderation request created",
                    extra={"request_id": request_id, "user_id": user_id},
                )
            except OpenRequestAlreadyExists:
                # This should not happen, but if it does, log a warning and continue
                current_app.logger.warning(
                    "User moderation request already exists", extra={"user_id": user_id}
                )
                raise

        current_app.logger.debug(
            "Updating user moderation request",
            extra={"request_id": request_id, "user_id": user_id},
        )
        req: Request = requests_service.record_cls.get_record(request_id)

        # If the request is closed or we want to moderate again, reopen it...
        if req.is_closed or action_ctx["action"] == "moderate":
            req.status = "submitted"
        else:
            # ...otherwise update the request based on the action
            if action_ctx["action"] == "block":
                req.status = "declined"
            elif action_ctx["action"] == "approve":
                req.status = "accepted"

        uow.register(RecordCommitOp(req, indexer=requests_service.indexer))

        # TODO: Generate content/links in a cleaner way
        # Add a comment with the moderation context (score, etc.)
        evaluation = action_ctx["evaluation"]
        content_pid = action_ctx.get("record_pid") or ""
        content = ""
        if content_pid.isdigit():
            content = f' (<a href="/records/{content_pid}">Record {content_pid}</a>)'
        else:
            content = (
                f' (<a href="/communities/{content_pid}">Community {content_pid}</a>)'
            )

        comment = dict(
            payload={"content": f"<p>Final evaluation: {evaluation}{content}</p>"}
        )
        events_service.create(system_identity, req, comment, CommentEventType, uow=uow)

        uow.commit()


@shared_task(ignore_result=True)
def run_moderation_handlers(user_id, record_id=None, community_id=None):
    """Run the content moderation handlers for a record or community."""
    user = users_service.record_cls.get_record(user_id)
    with UnitOfWork() as uow:
        if record_id is not None:
            handlers = current_app.config.get("RDM_CONTENT_MODERATION_HANDLERS")
            record = records_service.record_cls.get_record(record_id)
            for h in handlers:
                h.run(identity=None, record=record, user=user, uow=uow)

        elif community_id is not None:
            handlers = current_app.config.get(
                "RDM_COMMUNITY_CONTENT_MODERATION_HANDLERS"
            )
            community = current_communities.service.record_cls.get_record(community_id)
            for h in handlers:
                h.run(identity=None, record=community, user=user, uow=uow)

        uow.commit()
