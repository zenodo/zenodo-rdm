# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions stream."""

from uuid import UUID

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

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


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
