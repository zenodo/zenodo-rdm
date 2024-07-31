# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo community manage record request."""

from flask_login import current_user
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.proxies import (
    current_rdm_records_service,
    current_record_communities_service,
)
from invenio_rdm_records.records import RDMRecord
from invenio_records_resources.services.uow import IndexRefreshOp, RecordCommitOp
from invenio_requests.customizations import CommentEventType, RequestType, actions
from invenio_requests.proxies import current_events_service
from invenio_search.engine import dsl


def _remove_permission_flag(record, uow):
    """Remove can_community_manage_record permission flag."""
    try:
        record.parent.permission_flags.pop("can_community_manage_record")
        record.parent.commit()
        uow.register(RecordCommitOp(record.parent))
    except (KeyError, AttributeError):
        # if field or flag is absent just continue with an action
        pass


def _remove_record_from_communities(record, communities_ids):
    """Remove record from communities."""
    if communities_ids:
        communities = []
        for community_id in communities_ids:
            communities.append({"id": community_id})

        data = dict(communities=communities)
        current_record_communities_service.remove(system_identity, record["id"], data)


def _create_comment(request, content, uow):
    """Create a comment event."""
    comment = {"payload": {"content": content}}

    current_events_service.create(
        system_identity, request.id, comment, CommentEventType, uow=uow
    )

    # make event immediately available in search
    uow.register(IndexRefreshOp(indexer=current_events_service.indexer))


def _get_legacy_records_by_user():
    """Find legacy records of a specific user."""
    return current_rdm_records_service.search(
        system_identity,
        extra_filter=dsl.query.Bool(
            "must",
            must=[
                dsl.Q("terms", **{"parent.access.owned_by.user": [current_user.id]}),
                # indicator that record is a legacy one
                dsl.Q(
                    "exists",
                    field="parent.permission_flags.can_community_manage_record",
                ),
            ],
        ),
    )


def _resolve_record(legacy_record):
    """Get record byt its pid."""
    record_pid = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_value == legacy_record["id"]
    ).one()
    record_id = str(record_pid.object_uuid)
    return RDMRecord.get_record(record_id)


#
# Actions
#
class SubmitAction(actions.SubmitAction):
    """Submit action."""

    def execute(self, identity, uow):
        """Execute the submit action."""
        self.request["title"] = "Communities manage legacy records"

        # example: "May 11, 2024"
        expires_at = self.request.expires_at.strftime("%B %d, %Y")
        self.request["description"] = (
            "<h4>Some of your records, that are going through the migration process are part "
            "of communities that don't belong to you.</br>Accept this request to adopt the new "
            "behaviour and <b>allow community curators</b> to manage (edit, create new versions, add to "
            "another community, etc.) your corresponding records. </br>In case of declining this "
            "request all your legacy records will be <b>removed from all communities</b> "
            "that you are not an owner of. </br></br>If you do not perform any action by "
            f"<b>{expires_at}</b>, the permission for community curators to manage your records "
            "will automatically be fully granted.</h4>"
        )

        super().execute(identity, uow)


class AcceptAction(actions.AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        """Grant permission to manage all legacy records of a user to all the communities."""
        legacy_records = _get_legacy_records_by_user()

        for hit in legacy_records.hits:
            # remove flag from record parent, permissions logic will do the rest
            record = _resolve_record(hit)
            _remove_permission_flag(record, uow)

        comment = (
            "You accepted the request. The community curators "
            "can now manage all of your legacy records."
        )
        _create_comment(self.request, comment, uow)

        super().execute(identity, uow)


class DeclineAction(actions.DeclineAction):
    """Decline action."""

    def execute(self, identity, uow):
        """Deny access to manage legacy records for community curators."""
        legacy_records = _get_legacy_records_by_user()

        for legacy_record in legacy_records.hits:
            record = _resolve_record(legacy_record)
            communities = (
                legacy_record["parent"].get("communities", None).get("ids", None)
            )
            if communities is not None:
                my_communities = []
                for community_id in communities:
                    com_members = current_communities.service.members.search(
                        system_identity,
                        community_id,
                        extra_filter=dsl.query.Bool(
                            "must",
                            must=[
                                dsl.Q("term", **{"role": "owner"})
                                | dsl.Q("term", **{"role": "curator"}),
                                dsl.Q("term", **{"user_id": current_user.id}),
                            ],
                        ),
                    )
                    if com_members.total > 0:
                        my_communities.append(community_id)
                not_my_communities = list(set(communities) - set(my_communities))
                _remove_record_from_communities(record, not_my_communities)
            _remove_permission_flag(record, uow)

        super().execute(identity, uow)


class ExpireAction(actions.ExpireAction):
    """Expire action."""

    def execute(self, identity, uow):
        """Grant permission to manage all legacy records of a user to all the communities."""
        legacy_records = _get_legacy_records_by_user()

        for hit in legacy_records.hits:
            # remove flag from record parent, permissions logic will do the rest
            record = _resolve_record(hit)
            _remove_permission_flag(record, uow)

        comment = (
            "The request was expired. The community curators "
            "can now manage all of your legacy records."
        )
        _create_comment(self.request, comment, uow)

        super().execute(identity, uow)


#
# Request
#
class CommunityManageRecord(RequestType):
    """Request for granting permissions to manage a record for its community curators."""

    type_id = "community-manage-record"
    name = "Community manage record"

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
    topic_can_be_none = True

    allowed_creator_ref_types = ["user"]
    allowed_receiver_ref_types = ["user"]
