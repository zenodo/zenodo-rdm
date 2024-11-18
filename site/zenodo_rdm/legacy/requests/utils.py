# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility functions."""

from datetime import datetime, timedelta

from invenio_access.permissions import system_identity
from invenio_records.dictutils import dict_lookup
from invenio_records_resources.services.uow import unit_of_work
from invenio_requests import current_request_type_registry, current_requests_service
from invenio_requests.resolvers.registry import ResolverRegistry
from invenio_search.engine import dsl

from .community_manage_record import CommunityManageRecord
from .record_upgrade import LegacyRecordUpgrade
from ...subcommunities.request import ZenodoSubCommunityInvitationRequest


def exists(identity, record):
    """Return the request id if an open request already exists, else None."""
    results = current_requests_service.search(
        identity,
        extra_filter=dsl.query.Bool(
            "must",
            must=[
                dsl.Q("term", **{"topic.record": record.pid.pid_value}),
                dsl.Q("term", **{"type": LegacyRecordUpgrade.type_id}),
                dsl.Q("term", **{"is_open": True}),
            ],
        ),
    )
    return next(results.hits)["id"] if results.total > 0 else None


@unit_of_work()
def submit_record_upgrade_request(record, uow, comment=None):
    """Create and submit a LegacyRecordUpgrade request."""
    # check if record is migrated
    try:
        dict_lookup(record.parent, "permission_flags.can_community_read_files")
    except KeyError:
        raise Exception(
            "Legacy record upgrade request can't be created. The record is not a migrated one."
        )

    # check if there is already an open request, to avoid duplications
    if exists(system_identity, record):
        raise Exception(
            "There is already an open legacy record upgrade request for this record."
        )

    if record.access.protection.files == "public":
        raise Exception(
            "Legacy record upgrade request can't be created. The record doesn't have restricted files."
        )

    if not record.parent.communities.ids:
        raise Exception(
            "Legacy record upgrade request can't be created. The record doesn't belong to any community."
        )

    type_ = current_request_type_registry.lookup(LegacyRecordUpgrade.type_id)
    receiver = ResolverRegistry.resolve_entity_proxy(
        {"user": record.parent.access.owned_by.owner_id}
    ).resolve()
    expires_at = datetime.utcnow() + timedelta(days=365)

    # create a request
    request_item = current_requests_service.create(
        system_identity,
        {},
        type_,
        receiver,
        topic=record,
        expires_at=expires_at,
        uow=uow,
    )

    # submit the request
    return current_requests_service.execute_action(
        system_identity, request_item._request.id, "submit", data=comment, uow=uow
    )


@unit_of_work()
def submit_community_manage_record_request(user_id, uow, comment=None):
    """Create and submit a CommunityManageRecord request."""
    type_ = current_request_type_registry.lookup(CommunityManageRecord.type_id)
    receiver = ResolverRegistry.resolve_entity_proxy({"user": user_id}).resolve()
    expires_at = datetime.utcnow() + timedelta(weeks=20)

    # create a request
    request_item = current_requests_service.create(
        system_identity,
        {},
        type_,
        receiver,
        expires_at=expires_at,
        uow=uow,
    )

    # submit the request
    return current_requests_service.execute_action(
        system_identity, request_item._request.id, "submit", data=comment, uow=uow
    )


@unit_of_work()
def submit_join_as_subcommunity_request(
    parent_community_uuid, community_uuid, uow, comment=None
):
    """Create and submit a SubCommunityInvitation request."""
    type_ = current_request_type_registry.lookup(ZenodoSubCommunityInvitationRequest.type_id)
    creator = ResolverRegistry.resolve_entity_proxy(
        {"community": parent_community_uuid}
    ).resolve()
    receiver = ResolverRegistry.resolve_entity_proxy(
        {"community": community_uuid}
    ).resolve()
    expires_at = datetime.utcnow() + timedelta(days=30)

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
