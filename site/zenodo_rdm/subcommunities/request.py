# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Subcommunities request implementation for ZenodoRDM."""

import invenio_communities.notifications.builders as notifications
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_communities.subcommunities.services.request import (
    AcceptSubcommunity,
    AcceptSubcommunityInvitation,
    CreateSubcommunityInvitation,
    DeclineSubcommunity,
    DeclineSubcommunityInvitation,
    SubCommunityInvitationRequest,
    SubCommunityRequest,
)
from invenio_notifications.services.uow import NotificationOp
from invenio_rdm_records.proxies import (
    current_community_records_service,
    current_rdm_records,
)
from invenio_records_resources.services.uow import RecordCommitOp
from invenio_requests.customizations import actions
from invenio_requests.customizations.event_types import CommentEventType
from invenio_requests.proxies import current_events_service
from marshmallow import fields


def _add_community_records(child, parent, uow):
    """Add records from child to parent."""
    records = current_community_records_service.search(
        system_identity, community_id=child
    )
    current_rdm_records.record_communities_service.bulk_add(
        system_identity, parent, (x["id"] for x in records), uow=uow
    )


class SubcommunityAcceptAction(AcceptSubcommunity):
    """Represents an accept action used to accept a subcommunity.

    Zenodo re-implementation of the accept action, to also move the records.
    """

    def execute(self, identity, uow):
        """Execute approve action."""
        to_be_moved = self.request.topic.resolve().id
        move_to = self.request.receiver.resolve().id

        _add_community_records(to_be_moved, move_to, uow)
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


class SubcommunityInvitationCreateAction(CreateSubcommunityInvitation):
    """Represents an action to create and submit a subcommunity invitation."""

    def execute(self, identity, uow):
        """Execute approve action."""
        self.request["title"] = "Invitation to join the EU Open Research Repository"

        # example: "May 11, 2024"
        expires_at = self.request.expires_at.strftime("%B %d, %Y")
        NAME = self.request.get("payload", {}).get("community-name")
        ACRONYM = self.request.get("payload", {}).get("project-acronym")
        self.request["description"] = (
            "<p>We would like to invite you to join the <a href='https://zenodo.org/communities/eu/'>"
            "EU Open Research Repository</a> because we have detected that your Zenodo community "
            "is likely related to an EU-funded project:</br><ul><li>Zenodo community: "
            f"{NAME}</li><li>EU-funded project: {ACRONYM}</li></ul>The EU Open "
            "Research Repository is a Zenodo community dedicated to fostering open science "
            "and enhancing the visibility and accessibility of research outputs funded by "
            "the European Union. The community is managed by CERN on behalf of the European "
            "Commission.</br></br><b>What does it mean to join?</b></br><ul><li><b>Indexing:</b> "
            "All current and future records in your community will be automatically indexed "
            "in the EU Open Research Repository increasing their visibility</li><li><b>Curation:</b> "
            "All records will be subject to the EU Open Research Repository "
            "<a href='https://zenodo.org/communities/eu/curation-policy'>curation policy</a>. "
            "For instance, you can only deposit records in the community related to the EU-funded "
            "project</li><li><b>Verified:</b> All EU project communities are marked with a "
            "Verified community badge</li></ul>The EU Open Research Repository is gradually "
            "being improved and by mid-2025 new submissions will automatically be checked "
            "for compliance with the related open science requirements in the Horizon Europe "
            "grant agreement. For more information see <a href='https://zenodo.org/communities/eu/pages/join'>"
            "https://zenodo.org/communities/eu/pages/join</a>.</br></br><b>Which EU-funded projects "
            "have already joined?</b></br>You can browse the "
            "<a href='https://zenodo.org/communities/eu/browse/subcommunities'>EU-funded projects</a> "
            "which have already already joined.</br></br><b>When should I decline the invitation "
            "to join?</b></br>You should <b>decline</b> this invitation if your Zenodo community "
            "is not related to the above mentioned EU-funded project, or if the community is used "
            "for multiple purposes (e.g both an organisation and a project).</br></br><b>"
            "Further questions?</b></br>Don't hesitate to <a href='https://zenodo.org/support'>get in "
            "touch</a> with us if you have any questions.</br></br>The request will be automatically "
            f"accepted on <b>{expires_at}</b> in case you do not accept or decline the request by then."
            "</br></br>Yours sincerely,</br>The Zenodo team"
        )

        super().execute(identity, uow)


class SubCommunityInvitationAcceptAction(AcceptSubcommunityInvitation):
    """Represents an accept action used to accept a subcommunity.

    Zenodo re-implementation of the accept action, to also move the records.
    """

    def execute(self, identity, uow):
        """Execute approve action."""
        child = self.request.receiver.resolve().id
        parent = self.request.created_by.resolve().id

        _add_community_records(child, parent, uow)
        # moving the community is handled by super()

        super().execute(identity, uow)


class SubcommunityInvitationExpireAction(actions.ExpireAction):
    """Expire action."""

    def execute(self, identity, uow):
        """Execute expire action."""
        child = self.request.receiver.resolve().id
        parent = self.request.created_by.resolve().id

        _add_community_records(child, parent, uow)

        current_communities.service.bulk_update_parent(
            system_identity, [child], parent_id=parent, uow=uow
        )

        super().execute(identity, uow)

        uow.register(
            NotificationOp(
                notifications.SubComInvitationExpire.build(
                    identity=identity, request=self.request
                )
            )
        )


class ZenodoSubCommunityInvitationRequest(SubCommunityInvitationRequest):
    """Request from a Zenodo community to add a child community."""

    payload_schema = {
        "community-name": fields.String(required=True),
        "project-acronym": fields.String(required=True),
    }

    available_actions = {
        "delete": actions.DeleteAction,
        "cancel": actions.CancelAction,
        # Custom implemented actions
        "create": SubcommunityInvitationCreateAction,
        "accept": SubCommunityInvitationAcceptAction,
        "decline": DeclineSubcommunityInvitation,
        "expire": SubcommunityInvitationExpireAction,
    }
