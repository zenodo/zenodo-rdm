# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy record upgrade request."""

from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_record_communities_service
from invenio_records_resources.services.uow import IndexRefreshOp, RecordCommitOp
from invenio_requests.customizations import CommentEventType, RequestType, actions
from invenio_requests.proxies import current_events_service


def _remove_permission_flag(record, uow):
    """Remove can_community_read_files permission flag."""
    try:
        record.parent.permission_flags.pop("can_community_read_files")
        record.parent.commit()
        uow.register(RecordCommitOp(record.parent))
    except (KeyError, AttributeError):
        # if field or flag is absent just continue with an action
        pass


def _remove_record_from_communities(record, identity):
    """Remove record from all the communities."""
    communities_ids = record.parent.communities.ids
    communities = []
    for community_id in communities_ids:
        communities.append({"id": community_id})

    data = dict(communities=communities)
    current_record_communities_service.remove(identity, record["id"], data)


def _create_comment(request, content, uow):
    """Create a comment event."""
    comment = {"payload": {"content": content}}

    current_events_service.create(
        system_identity, request.id, comment, CommentEventType, uow=uow
    )

    # make event immediately available in search
    uow.register(IndexRefreshOp(indexer=current_events_service.indexer))


#
# Actions
#
class SubmitAction(actions.SubmitAction):
    """Submit action."""

    def execute(self, identity, uow):
        """Execute the submit action."""
        record = self.request.topic.resolve()
        record_title = record.metadata["title"]
        self.request["title"] = f"Upgrade your legacy record: {record_title}"

        # example: "May 11, 2024"
        expires_at = self.request.expires_at.strftime("%B %d, %Y")
        self.request["description"] = (
            "The current record uses legacy behavior which has been removed from "
            "the platform, and needs to be upgraded. Upgrading the record "
            "will have the following impact:"
            "<ul><li><b>Access: </b>curators of communities that this record "
            "is part of will be granted view and edit access to your record (i.e. curators can see restricted "
            "files and edit metadata)</li></ul>"
            f"If you do not upgrade the record by <b>{expires_at}</b>, it will "
            "be automatically <u>removed from its communities</u>."
        )

        super().execute(identity, uow)


class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        """Grant access to restricted files of a record for a community."""
        record = self.request.topic.resolve()

        # remove flag from record parent, permissions logic will do the rest
        _remove_permission_flag(record, uow)

        comment = (
            "You accepted the request. The record is now upgraded and all the communities"
            " that this record belongs to will now have access to the restricted files."
        )
        _create_comment(self.request, comment, uow)
        super().execute(identity, uow)


class DeclineAction(actions.DeclineAction):
    """Decline action."""

    def execute(self, identity, uow):
        """Deny access to restricted files of a record for all the communities."""
        record = self.request.topic.resolve()

        # remove the flag
        _remove_permission_flag(record, uow)

        comment = {}

        # it looks like the uploader changed the restriction of files after the request was already open
        files_already_public = record.access.protection.files == "public"
        if files_already_public:
            comment = "As a result of decline action record was not removed from its communities because it doesn't have restricted files."
        elif not record.parent.communities.ids:
            # it looks like the uploader removed the record from all communities after the request was already open
            comment = "As a result of decline action record was not removed from its communities because it doesn't belong to any."

        if comment:
            _create_comment(self.request, comment, uow)
        else:
            # remove record from all the communities
            _remove_record_from_communities(record, identity)

        super().execute(identity, uow)


class ExpireAction(actions.ExpireAction):
    """Expire action."""

    def execute(self, identity, uow):
        """Deny access to restricted files of a record for all the communities."""
        record = self.request.topic.resolve()

        # remove the flag
        _remove_permission_flag(record, uow)

        # Note: in case if this request is submitted but not resolved yet, and current record
        # is added to new communities then the access to restricted files of a record for those
        # communities will still depend on the request's logic. Apart from that, the record will still
        # be removed from new communities in case of request declining or expiring.
        if (
            record.access.protection.files == "restricted"
            and record.parent.communities.ids
        ):
            _remove_record_from_communities(record, identity)

        super().execute(identity, uow)


#
# Request
#
class LegacyRecordUpgrade(RequestType):
    """Legacy record upgrade request for managing community access to restricted files of a record."""

    type_id = "legacy-record-upgrade"
    name = "Upgrade legacy record"

    available_actions = {
        "create": actions.CreateAction,
        "submit": SubmitAction,
        "delete": actions.DeleteAction,
        "accept": AcceptAction,
        "cancel": actions.CancelAction,
        "decline": DeclineAction,
        "expire": ExpireAction,
    }

    creator_can_be_none = False
    topic_can_be_none = False

    allowed_creator_ref_types = ["user"]
    allowed_receiver_ref_types = ["user"]
    allowed_topic_ref_types = ["record"]
