# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Subcommunities request implementation for ZenodoRDM."""

from invenio_access.permissions import system_identity
from invenio_communities.subcommunities.services.request import (
    AcceptSubcommunity,
    DeclineSubcommunity,
    SubCommunityRequest,
)
from invenio_rdm_records.proxies import (
    current_community_records_service,
    current_rdm_records,
)
from invenio_requests.customizations import actions


class ZenodoSubcommunityAccept(AcceptSubcommunity):
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
            system_identity, move_to, (x['id'] for x in records), uow=uow
        )
        super().execute(identity, uow)


class ZenodoSubCommunityRequest(SubCommunityRequest):
    """Request to add a subcommunity to a Zenodo community."""

    available_actions = {
        "delete": actions.DeleteAction,
        "create": actions.CreateAndSubmitAction,
        "cancel": actions.CancelAction,
        "accept": ZenodoSubcommunityAccept,
        "decline": DeclineSubcommunity,
    }
