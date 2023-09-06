# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions stream."""

from uuid import UUID

import pytest
import sqlalchemy as sa
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.files import FilesBucket
from invenio_rdm_migrator.streams.models.pids import PersistentIdentifier
from invenio_rdm_migrator.streams.models.records import (
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMVersionState,
)

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture()
def db_draft(database, session):
    # since there are not FKs in the test database there is no need for PID, Buckets, etc.
    records = [
        RDMParentMetadata(
            id="9493793c-47d2-48e2-9867-ca597b4ebb41",
            json={
                "id": "1217214",
                "pid": {"pk": 2, "pid_type": "recid", "status": "R", "obj_type": "rec"},
                "access": {"owned_by": {"user": 1234}},
                "communities": {"ids": ["zenodo"], "default": "zenodo"},
            },
            version_id=1,
            created="2021-05-01T00:00:00",
            updated="2021-05-01T00:00:00",
        ),
        RDMDraftMetadata(
            id="d94f793c-47d2-48e2-9867-ca597b4ebb41",
            json={
                "id": "1217215",
                "$schema": "https://zenodo.org/schemas/deposits/records/record-v1.0.0.json",
                "pids": {},
                "files": {"enabled": True},
                "metadata": {"title": "fixture title"},
                "access": {
                    "record": "public",
                    "files": "public",
                },
                "custom_fields": {},
            },
            created="2021-05-01T00:00:00",
            updated="2021-05-01T00:00:00",
            version_id=1,
            index=1,
            bucket_id="0e12b4b6-9cc7-46df-9a04-c11c478de211",
            media_bucket_id=None,
            parent_id="9493793c-47d2-48e2-9867-ca597b4ebb41",
            expires_at="2024-05-01T00:00:00",
            fork_version_id=None,
        ),
    ]

    for obj in records:
        session.add(obj)
    session.commit()


@pytest.fixture()
def parent_state(state):
    state.PARENTS.add(
        "1217214",  # recid
        {
            "id": "9493793c-47d2-48e2-9867-ca597b4ebb41",
            "next_draft_id": "d94f793c-47d2-48e2-9867-ca597b4ebb41",
        },
    )


def test_draft_create_action_stream(
    state,
    database,
    session,
    test_extract_cls,
    create_draft_tx,
    pg_tx_load,
):
    """Test draft create action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(create_draft_tx),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    # PIDs
    pids = session.scalars(sa.select(PersistentIdentifier)).all()
    assert len(pids) == 2
    assert {p.pid_value for p in pids} == {"1217214", "1217215"}

    # Bucket
    bucket = session.scalars(sa.select(FilesBucket)).one()
    assert bucket.id == UUID("0e12b4b6-9cc7-46df-9a04-c11c478de211")

    # Draft parent and versioning
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()

    assert draft.created == "2023-06-29T13:38:48.842023"
    assert draft.updated == "2023-06-29T13:38:48.842023"

    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    assert parent.created == "2023-06-29T13:38:48.842023"
    assert parent.updated == "2023-06-29T13:38:48.842023"

    versioning = session.scalars(sa.select(RDMVersionState)).one()
    assert parent.id == draft.parent_id == versioning.parent_id
    assert draft.id == versioning.next_draft_id


def test_draft_edit_action_stream(
    parent_state,
    session,
    db_draft,
    test_extract_cls,
    update_draft_tx,
    pg_tx_load,
):
    """Test draft edit action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(update_draft_tx),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    # Draft parent and versioning
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    assert draft.created == "2021-05-01T00:00:00"
    assert draft.updated == "2023-06-29T13:00:00"
    assert draft.json["metadata"]["title"] == "update test"

    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    assert parent.created == "2021-05-01T00:00:00"
    assert parent.updated == "2023-06-29T13:00:00"


def test_draft_partial_edit_action_stream(
    parent_state,
    session,
    db_draft,
    test_extract_cls,
    update_draft_tx,
    pg_tx_load,
):
    """Test draft partial edit action."""
    # make it a partial update
    update_draft_tx["operations"][0]["after"] = {
        "updated": "2023-07-01T13:00:00",
        "id": "b7547ab1-47d2-48e2-9867-ca597b4ebb41",
        "json": '{"doi": "","recid": 1217215,"title": "update partial test","$schema": "https://zenodo.org/schemas/deposits/records/record-v1.0.0.json","license": {"$ref": "https://dx.zenodo.org/licenses/CC-BY-4.0"},"_buckets": {"deposit": "0e12b4b6-9cc7-46df-9a04-c11c478de211"},"_deposit": {"owners": [86261],"status": "draft","created_by": 86261},"creators": [{"name": "me"}],"description": "<p>testing</p>","access_right": "open","conceptrecid": "1217214","resource_type": {"type": "publication", "subtype": "article"},"publication_date": "2023-06-29"}',
    }
    stream = Stream(
        name="action",
        extract=test_extract_cls(update_draft_tx),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    # Draft parent and versioning
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    assert draft.created == "2021-05-01T00:00:00"
    assert draft.updated == "2023-07-01T13:00:00"
    assert draft.json["metadata"]["title"] == "update partial test"

    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    assert parent.created == "2021-05-01T00:00:00"
    # this is not a 100% true since the parent might not be updated
    # to fix it, we could store this in the state, on the other hand
    # it does not affect the workflows of the system and it makes the code
    # easier/more readable
    assert parent.updated == "2023-07-01T13:00:00"
