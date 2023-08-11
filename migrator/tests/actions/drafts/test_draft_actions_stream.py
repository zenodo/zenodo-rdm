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
from invenio_rdm_migrator.load.postgresql.transactions import PostgreSQLTx
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.files import FilesBucket
from invenio_rdm_migrator.streams.models.pids import PersistentIdentifier
from invenio_rdm_migrator.streams.models.records import (
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMVersionState,
)
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture()
def db_draft(db_engine):
    # since there are not FKs in the test database there is no need for PID, Buckets, etc.
    history = [
        RDMParentMetadata(
            id="9493793c-47d2-48e2-9867-ca597b4ebb41",
            json={
                "id": "1217214",
                "pid": {"pk": 2, "pid_type": "recid", "status": "R", "obj_type": "rec"},
                "access": {"owned_by": [{"user": 1234}]},
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
            parent_id="9493793c-47d2-48e2-9867-ca597b4ebb41",
            expires_at="2024-05-01T00:00:00",
            fork_version_id=None,
        ),
    ]

    with Session(db_engine) as session:
        for obj in history:
            session.add(obj)
        session.commit()

    yield

    # cleanup
    with Session(db_engine) as session:
        for obj in history:
            session.delete(obj)

        try:
            session.commit()
        except ObjectDeletedError:  # might be deleted on user inactivation
            pass


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
    state, test_extract_cls, create_draft_tx, db_uri, db_engine
):
    """Creates a DB on disk and initializes all the migrator related tables on it."""
    # test

    test_extract_cls.tx = create_draft_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        # PIDs
        pids = list(conn.execute(sa.select(PersistentIdentifier)))
        assert len(pids) == 2

        pid_values = {"1217214", "1217215"}
        db_pid_values = set(map(lambda row: row._mapping["pid_value"], pids))
        assert db_pid_values == pid_values

        # Bucket
        buckets = list(conn.execute(sa.select(FilesBucket)))
        assert len(buckets) == 1

        assert buckets[0]._mapping["id"] == UUID("0e12b4b6-9cc7-46df-9a04-c11c478de211")

        # Draft parent and versioning
        drafts = list(conn.execute(sa.select(RDMDraftMetadata)))
        assert len(drafts) == 1

        draft = drafts[0]._mapping
        assert draft["created"] == "2023-06-29T13:38:48.842023"
        assert draft["updated"] == "2023-06-29T13:38:48.842023"

        parents = list(conn.execute(sa.select(RDMParentMetadata)))
        assert len(parents) == 1

        parent = parents[0]._mapping
        assert parent["created"] == "2023-06-29T13:38:48.842023"
        assert parent["updated"] == "2023-06-29T13:38:48.842023"

        versioning = list(conn.execute(sa.select(RDMVersionState)))
        assert len(versioning) == 1

        versioning = versioning[0]._mapping

        assert parent["id"] == draft["parent_id"] == versioning["parent_id"]
        assert draft["id"] == versioning["next_draft_id"]


def test_draft_edit_action_stream(
    parent_state, db_draft, test_extract_cls, update_draft_tx, db_uri, db_engine
):
    """Creates a DB on disk and initializes all the migrator related tables on it."""
    # test

    test_extract_cls.tx = update_draft_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        # Draft parent and versioning
        drafts = list(conn.execute(sa.select(RDMDraftMetadata)))
        assert len(drafts) == 1

        draft = drafts[0]._mapping
        assert draft["created"] == "2021-05-01T00:00:00"
        assert draft["updated"] == "2023-06-29T13:00:00"
        assert draft["json"]["metadata"]["title"] == "update test"

        parents = list(conn.execute(sa.select(RDMParentMetadata)))
        assert len(parents) == 1

        parent = parents[0]._mapping
        assert parent["created"] == "2021-05-01T00:00:00"
        assert parent["updated"] == "2023-06-29T13:00:00"
