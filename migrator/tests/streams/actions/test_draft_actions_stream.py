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
from invenio_rdm_migrator.extract import Extract, Tx
from invenio_rdm_migrator.load.postgresql.transactions import PostgreSQLTx
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.files import FilesBucket
from invenio_rdm_migrator.streams.models.pids import PersistentIdentifier
from invenio_rdm_migrator.streams.models.records import (
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMVersionState,
)
from invenio_rdm_migrator.transform import BaseTxTransform

from zenodo_rdm_migrator.actions import ZenodoDraftCreateAction


@pytest.fixture()
def test_extract_cls(create_draft_tx):
    class TestExtractor(Extract):
        """Test extractor."""

        def run(self):
            """Yield one element at a time."""
            yield Tx(
                id=create_draft_tx["tx_id"], operations=create_draft_tx["operations"]
            )

    return TestExtractor


@pytest.fixture()
def test_transform_cls(create_draft_tx):
    class TestTxTransform(BaseTxTransform):
        """Test transform class."""

        actions = [
            ZenodoDraftCreateAction,
        ]

    return TestTxTransform


DB_URI = "postgresql://invenio:invenio@localhost:5432/invenio"


@pytest.fixture(scope="function")
def db_engine():
    tables = [
        PersistentIdentifier,
        FilesBucket,
        RDMDraftMetadata,
        RDMParentMetadata,
        RDMVersionState,
    ]
    eng = sa.create_engine(DB_URI)

    # create tables
    for model in tables:
        model.__table__.create(bind=eng, checkfirst=True)

    yield eng

    # remove tables
    for model in tables:
        model.__table__.drop(eng)


def test_draft_create_action_stream(test_extract_cls, test_transform_cls, db_engine):
    """Creates a DB on disk and initializes all the migrator related tables on it."""
    # test

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=test_transform_cls(),
        load=PostgreSQLTx(DB_URI),
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

        parents = list(conn.execute(sa.select(RDMParentMetadata)))
        assert len(parents) == 1

        versioning = list(conn.execute(sa.select(RDMVersionState)))
        assert len(versioning) == 1

        parent = parents[0]._mapping
        draft = drafts[0]._mapping
        versioning = versioning[0]._mapping

        assert parent["id"] == draft["parent_id"] == versioning["parent_id"]
        assert draft["id"] == versioning["next_draft_id"]
