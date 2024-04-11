# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Script to transfer communities and records under a new community.

Usage:

.. code-block:: python

    _to = "ec_community"
    _from = ["one_eu_project", "another_maybe"]

    # option 1 - move communities to new parent (including records)
    transfer_communities(identity, _from, _to, set_default=False)

    # option 2 - move records in bulk
    records = ["1234561", "1234321"]
    transfer_records(identity, records, _to, set_default=False)

"""

from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records
from invenio_records_resources.services.uow import UnitOfWork
from invenio_search.engine import dsl
from werkzeug.local import LocalProxy

community_service = LocalProxy(lambda: current_communities.service)
records_communities_service = LocalProxy(
    lambda: current_rdm_records.record_communities_service
)
records_service = LocalProxy(lambda: current_rdm_records.records_service)


def _all_records_q(community_ids):
    """Auxiliary function that creates a query to filter records by community ids.

    Fetches the latest versions of the records only.

    :param community_ids: The list of community ids to filter the records by.
    """
    extra_filter = dsl.query.Bool(
        "must",
        must=[
            dsl.Q("terms", **{"parent.communities.ids": community_ids}),
            dsl.Q("term", **{"versions.is_latest": True}),
        ],
    )

    return extra_filter


def _search_records(identity, records_q):
    """Create a search object for records and returns the record ids using a scan() query."""
    search = records_service.create_search(
        identity,
        records_service.record_cls,
        records_service.config.search,
        permission_action="read",
        extra_filter=records_q,
    )

    yield from map(lambda x: x.id, search.scan())


def transfer_communities(
    identity,
    community_ids,
    parent_community_id,
    records_q=None,
    set_default=False,
):
    """Transfer communities and records to new parent.

    Usage 1 - transfer all the records:

    .. code-block:: python

        identity = ...
        community_ids = ["a_small_eu_project", "test_eu_project"]
        parent_community_id = "the_eu_community"
        transfer_communities(identity, community_ids, parent_community_id)

    Usage 2 - transfer only the records that match a specific query and set the new parent as default:

    .. code-block:: python

        identity = ...
        community_ids = ["a_small_eu_project", "test_eu_project"]
        parent_community_id = "the_eu_community"
        records_q = dsl.query.Bool(
            "must",
            must=[
                dsl.Q("terms", **{"parent.communities.ids": community_ids}),
                dsa.Q("term", **{"metadata.publication_date": ""})
            ],
        )
        transfer_communities(
            identity, community_ids, parent_community_id, records_q, set_default=True
        )

    :param identity: Identity of the user performing the action.
    :param community_ids: List of community IDs to transfer.
    :param parent_community_id: New parent community ID to transfer the communities to.
    :param records_q: The query to filter the records to transfer. If not provided, all the records will be transferred.
    :param set_default: Whether to set the parent as the default community of the records. Default is False.
    """
    if not records_q:
        c_ids = [community_service.record_cls.pid.resolve(x).id for x in community_ids]
        records_q = _all_records_q(c_ids)

    with UnitOfWork() as uow:
        # Step 1 -  move communities to new target using communities service
        community_service.bulk_update_parent(
            identity, community_ids, parent_community_id, uow=uow
        )

        # Step 2 - move records to new parent using community records service
        record_ids = _search_records(identity, records_q)
        records_communities_service.bulk_add(
            identity, parent_community_id, record_ids, set_default=set_default, uow=uow
        )
        uow.commit()


def transfer_records(identity, record_ids, community_id, set_default=False):
    """Transfer records to a community.

    Usage:

    .. code-block:: python

            identity = ...
            record_ids = ["1234561", "1234321"]
            community_id = "the_eu_community"
            transfer_records(identity, record_ids, community_id)

    :param identity: Identity of the user performing the action.
    :param record_ids: List of record IDs to transfer.
    :param community_id: Community ID to transfer the records to.
    :param set_default: Whether to set the community as the default community of the records. Default is False.
    """
    with UnitOfWork() as uow:
        records_communities_service.bulk_add(
            identity, community_id, record_ids, set_default=set_default, uow=uow
        )
        uow.commit()
