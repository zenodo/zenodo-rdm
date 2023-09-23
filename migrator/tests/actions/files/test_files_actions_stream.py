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
from invenio_rdm_migrator.streams.models.files import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)
from invenio_rdm_migrator.streams.models.records import RDMDraftFile

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture(scope="function")
def db_bucket(database, session):
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

    bucket_obj = FilesBucket(**bucket_data)
    session.add(bucket_obj)
    session.commit()


def test_draft_create_action_stream(
    buckets_state,
    db_bucket,
    test_extract_cls,
    pg_tx_load,
    file_upload_tx,
    session,
):
    """Creates a DB on disk and initializes all the migrator related tables on it."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(file_upload_tx),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    bucket = session.scalars(sa.select(FilesBucket)).one()
    assert bucket.id == UUID("0e12b4b6-9cc7-46df-9a04-c11c478de211")
    # check the latest update time
    assert bucket.updated.isoformat() == "2023-06-29T14:00:00"

    ov = session.scalars(sa.select(FilesObjectVersion)).one()
    assert ov.version_id == UUID("f8200dc7-55b6-4785-abd0-f3d13b143c98")
    # check the latest update time
    assert ov.updated.isoformat() == "2023-06-29T14:00:00"

    fi = session.scalars(sa.select(FilesInstance)).one()
    assert fi.id == UUID("e94b243e-9c0c-44df-bd1f-6decc374cf78")
    # check the latest update time
    assert fi.updated.isoformat() == "2023-06-29T14:00:00"

    fr = session.scalars(sa.select(RDMDraftFile)).one()
    assert fr.record_id == UUID("d94f793c-47d2-48e2-9867-ca597b4ebb41")
