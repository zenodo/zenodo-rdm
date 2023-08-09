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
from invenio_rdm_migrator.streams.models.files import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)
from invenio_rdm_migrator.streams.models.records import RDMDraftFile
from sqlalchemy.orm import Session

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture(scope="function")
def db_bucket(db_engine):
    bucket_data = {
        "created": "2023-06-29T13:00:00",
        "updated": "2023-06-29T14:00:00",  # touch the bucket, modify updated
        "id": "0e12b4b6-9cc7-46df-9a04-c11c478de211",
        "default_location": 1,
        "default_storage_class": "S",
        "size": 0,
        "quota_size": 50000000000,
        "max_file_size": 50000000000,
        "locked": False,
        "deleted": False,
    }

    history = []
    with Session(db_engine) as session:
        bucket_obj = FilesBucket(**bucket_data)
        history.append(bucket_obj)
        session.add(bucket_obj)
        session.commit()

    yield

    # cleanup
    with Session(db_engine) as session:
        for obj in history:
            session.delete(obj)
        session.commit()


def test_draft_create_action_stream(
    buckets_state, db_bucket, test_extract_cls, file_upload_tx, db_uri, db_engine
):
    """Creates a DB on disk and initializes all the migrator related tables on it."""
    test_extract_cls.tx = file_upload_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        buckets = conn.execute(sa.select(FilesBucket)).fetchall()
        assert len(buckets) == 1
        assert buckets[0]._mapping["id"] == UUID("0e12b4b6-9cc7-46df-9a04-c11c478de211")
        # check the latest update time
        assert buckets[0]._mapping["updated"] == "2023-06-29T14:00:00"

        ovs = conn.execute(sa.select(FilesObjectVersion)).fetchall()
        assert len(ovs) == 1
        assert ovs[0]._mapping["version_id"] == UUID(
            "f8200dc7-55b6-4785-abd0-f3d13b143c98"
        )
        # check the latest update time
        assert ovs[0]._mapping["updated"] == "2023-06-29T14:00:00"

        fis = conn.execute(sa.select(FilesInstance)).fetchall()
        assert len(fis) == 1
        assert fis[0]._mapping["id"] == UUID("e94b243e-9c0c-44df-bd1f-6decc374cf78")
        # check the latest update time
        assert fis[0]._mapping["updated"] == "2023-06-29T14:00:00"

        frs = conn.execute(sa.select(RDMDraftFile)).fetchall()
        assert len(frs) == 1
        assert frs[0]._mapping["record_id"] == UUID(
            "d94f793c-47d2-48e2-9867-ca597b4ebb41"
        )
