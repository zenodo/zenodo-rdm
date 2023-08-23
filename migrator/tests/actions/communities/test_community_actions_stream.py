# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test community actions stream."""

import pytest
import sqlalchemy as sa
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.communities import Community, CommunityMember
from invenio_rdm_migrator.streams.models.files import FilesBucket
from invenio_rdm_migrator.streams.models.oai import OAISet

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture(scope="function")
def db_community(database, db_user, session, state):
    bucket_obj = FilesBucket(
        id="0e12b4b6-9cc7-46df-9a04-c11c478de211",
        created="2023-08-01T16:14:06.964000",
        updated="2023-08-01T16:14:06.964000",
        default_location=1,
        default_storage_class="L",
        size=0,
        quota_size=50000000000,
        max_file_size=50000000000,
        locked=False,
        deleted=False,
    )

    comm_obj = Community(
        id="cdd2b870-2846-468c-9574-79380a73326b",
        created="2023-08-01T16:14:06.964000",
        updated="2023-08-01T16:14:06.964000",
        slug="comm",
        bucket_id=bucket_obj.id,
        json={
            "files": {"enabled": True},
            "access": {
                "visibility": "public",
                "member_policy": "open",
                "record_policy": "open",
            },
            "metadata": {
                "page": "",
                "title": "Test community",
                "curation_policy": "",
                "description": "Testing community",
            },
        },
        version_id=1,
    )

    oai_set_obj = OAISet(
        id=123,
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
        spec="community-comm",
        name="Test community",
        description="Test community description",
        search_pattern=f"parent.communities.ids:{comm_obj.id}",
        system_created=True,
    )

    comm_member_obj = CommunityMember(
        user_id=db_user.id,
        created="2023-01-01T12:00:00.00000",
        updated="2023-01-31T12:00:00.00000",
        json={},
        version_id=1,
        role="owner",
        visible=True,
        active=True,
        group_id=None,
        request_id=None,
    )

    session.add(comm_obj)
    session.add(bucket_obj)
    session.add(comm_member_obj)
    session.add(oai_set_obj)
    session.commit()

    state.COMMUNITIES.add(
        comm_obj.slug,
        {
            "id": comm_obj.id,
            "bucket_id": comm_obj.bucket_id,
            "oai_set_id": oai_set_obj.id,
            "community_file_id": None,
            "logo_object_version_id": None,
        },
    )


def test_community_create_action_stream(
    secret_keys_state,
    database,
    session,
    pg_tx_load,
    test_extract_cls,
    tx_files,
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["create"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    bucket = session.scalars(sa.select(FilesBucket)).one()
    assert bucket

    community = session.scalars(sa.select(Community)).one()
    assert community.slug == "migration-test"
