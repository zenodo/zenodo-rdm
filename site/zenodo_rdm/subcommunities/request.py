# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Subcommunities request implementation for ZenodoRDM."""

from datetime import datetime, timedelta, timezone

import invenio_communities.notifications.builders as notifications
from invenio_access.permissions import system_identity
from invenio_communities.subcommunities.services.request import (
    AcceptSubcommunity,
    DeclineSubcommunity,
    SubCommunityInvitationRequest,
    SubCommunityRequest,
)
from invenio_notifications.services.uow import NotificationOp
from invenio_rdm_records.proxies import (
    current_community_records_service,
    current_rdm_records,
)
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work
from invenio_requests import current_request_type_registry, current_requests_service
from invenio_requests.customizations import actions
from invenio_requests.customizations.event_types import CommentEventType
from invenio_requests.proxies import current_events_service
from invenio_requests.resolvers.registry import ResolverRegistry
from marshmallow import fields


class SubcommunityAcceptAction(AcceptSubcommunity):
    """Represents an accept action used to accept a subcommunity.

    Zenodo re-implementation of the accept action, to also move the records.
    """

    def _get_community_records(self, community_id):
        """Get the records of a community."""
        return current_community_records_service.search(
            system_identity, community_id=community_id
        )

    def execute(self, identity, uow):
        """Execute approve action."""
        to_be_moved = self.request.topic.resolve().id
        move_to = self.request.receiver.resolve().id

        # Move records
        records = self._get_community_records(to_be_moved)
        current_rdm_records.record_communities_service.bulk_add(
            system_identity, move_to, (x["id"] for x in records), uow=uow
        )
        super().execute(identity, uow)


class SubcommunityCreateAction(actions.CreateAndSubmitAction):
    """Represents an create action used to create a subcommunity request.

    Zenodo re-implementation of the create action, to also create the system comment.
    """

    def _update_subcommunity_funding(self, subcommunity, uow):
        """Update the subcommunity funding metadata."""
        project_id = self.request.get("payload", {}).get("project_id")
        if not project_id:
            return

        funding = subcommunity.metadata.setdefault("funding", [])
        if project_id in [f.get("award", {}).get("id") for f in funding]:
            return subcommunity

        funder_id, _ = project_id.split("::", 1)
        funding.append({"award": {"id": project_id}, "funder": {"id": funder_id}})
        uow.register(RecordCommitOp(subcommunity))
        return subcommunity

    def execute(self, identity, uow):
        """Execute create action."""
        subcommunity = self.request.topic.resolve()

        self._update_subcommunity_funding(subcommunity, uow)

        # Execute the default create action
        super().execute(identity, uow)

        # Create a system comment
        comment_data = dict(
            payload={
                "content": f"""
            <p>
            We have created your community for your project <a href='/communities/{subcommunity.slug}'>{subcommunity['metadata']['title']}</a>.
            </p>

            <p>
            While we review your request, you can get started using your community by:
            <ul>
                <li><a href="https://help.zenodo.org/docs/communities/manage-community-settings/edit-profile/">Edit your community profile</a>, to add a logo and other information.</li>
                <li><a href="https://help.zenodo.org/docs/communities/manage-members/">Invite new members</a> to join your community.</li>
                <li>Learn more about how to <a href="https://help.zenodo.org/docs/communities/review-submissions/"> review submissions</a> and <a href="https://help.zenodo.org/docs/communities/curate/">curate records.</a></li>
            </ul>
            </p>
            """
            }
        )
        current_events_service.create(
            system_identity,
            self.request,
            comment_data,
            CommentEventType,
            uow=uow,
        )


class ZenodoSubCommunityRequest(SubCommunityRequest):
    """Request to add a subcommunity to a Zenodo community."""

    payload_schema = {"project_id": fields.String()}

    available_actions = {
        "delete": actions.DeleteAction,
        "cancel": actions.CancelAction,
        # Custom implemented actions
        "create": SubcommunityCreateAction,
        "accept": SubcommunityAcceptAction,
        "decline": DeclineSubcommunity,
    }


class SubCommunityInvitationAcceptAction(AcceptSubcommunity):
    """Represents an accept action used to accept a subcommunity.

    Zenodo re-implementation of the accept action, to also move the records.
    """

    def _get_community_records(self, community_id):
        """Get the records of a community."""
        return current_community_records_service.search(
            system_identity, community_id=community_id
        )

    def execute(self, identity, uow):
        """Execute approve action."""
        to_be_moved = self.request.topic.resolve().id
        move_to = self.request.receiver.resolve().id

        # Move records
        records = self._get_community_records(to_be_moved)
        current_rdm_records.record_communities_service.bulk_add(
            system_identity, move_to, (x["id"] for x in records), uow=uow
        )
        super().execute(identity, uow)


class SubcommunityInvitationSubmitAction(actions.SubmitAction):
    """Submit action."""

    def execute(self, identity, uow):
        """Execute the submit action."""
        self.request["title"] = "Invitation to join the EU Open Research Repository"

        # example: "May 11, 2024"
        expires_at = self.request.expires_at.strftime("%B %d, %Y")
        self.request["description"] = (
            "<p><br><br>If you do not perform any action by <b>{expires_at}</b>, the permission for "
            "community curators, managers and owners to manage your records will be automatically granted.</p>"
        )

        super().execute(identity, uow)


class SubcommunityInvitationExpireAction(actions.ExpireAction):
    """Expire action."""

    def execute(self, identity, uow):
        """Accepts the request."""

        super().execute(identity, uow)


class ZenodoSubCommunityInvitationRequest(SubCommunityInvitationRequest):
    """Request from a Zenodo community to add a child community."""

    available_actions = {
        "create": actions.CreateAction,
        "delete": actions.DeleteAction,
        "cancel": actions.CancelAction,
        # Custom implemented actions
        "submit": SubcommunityInvitationSubmitAction,
        "accept": SubcommunityAcceptAction,
        "decline": DeclineSubcommunity,
        "expire": SubcommunityInvitationExpireAction,
    }


@unit_of_work()
def submit_join_as_subcommunity_request(
    parent_community_uuid, community_uuid, uow, comment=None
):
    """Create and submit a SubCommunityInvitation request."""
    type_ = current_request_type_registry.lookup(
        ZenodoSubCommunityInvitationRequest.type_id
    )
    creator = ResolverRegistry.resolve_entity_proxy(
        {"community": parent_community_uuid}
    ).resolve()
    receiver = ResolverRegistry.resolve_entity_proxy(
        {"community": community_uuid}
    ).resolve()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    request_item = current_requests_service.create(
        system_identity,
        {},
        type_,
        receiver,
        creator=creator,
        expires_at=expires_at,
        uow=uow,
    )

    return current_requests_service.execute_action(
        system_identity, request_item._request.id, "submit", data=comment, uow=uow
    )
