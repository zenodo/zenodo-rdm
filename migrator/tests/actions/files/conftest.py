# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

import pytest
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType


@pytest.fixture()
def file_upload_tx():
    """Transaction data to publish a draft.

    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724580,
        "operations": [
            {
                "after": {
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
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045933202,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829808184","1375829808224"]',
                    "schema": "public",
                    "table": "files_bucket",
                    "txId": 533724612,
                    "lsn": 1375829808224,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1688045933693,
                "transaction": None,
            },
            {
                "after": {
                    "created": "2023-06-29T13:00:00",
                    "updated": "2023-06-29T13:00:00",
                    "bucket_id": "0e12b4b6-9cc7-46df-9a04-c11c478de211",
                    "key": "IMG_3535.jpg",
                    "version_id": "f8200dc7-55b6-4785-abd0-f3d13b143c98",
                    "file_id": None,
                    "_mimetype": None,
                    "is_head": True,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045933202,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829808184","1375829808360"]',
                    "schema": "public",
                    "table": "files_object",
                    "txId": 533724612,
                    "lsn": 1375829808360,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
                "ts_ms": 1688045933693,
                "transaction": None,
            },
            {
                "after": {
                    "created": "2023-06-29T13:00:00",
                    "updated": "2023-06-29T13:00:00",
                    "id": "e94b243e-9c0c-44df-bd1f-6decc374cf78",
                    "uri": None,
                    "storage_class": None,
                    "size": 0,
                    "checksum": None,
                    "readable": False,
                    "writable": True,
                    "last_check_at": None,
                    "last_check": True,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045933202,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829808184","1375829826872"]',
                    "schema": "public",
                    "table": "files_files",
                    "txId": 533724612,
                    "lsn": 1375829826872,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
                "ts_ms": 1688045933693,
                "transaction": None,
            },
            {
                "after": {
                    "created": "2023-06-29T13:00:00",
                    "updated": "2023-06-29T14:00:00",
                    "bucket_id": "0e12b4b6-9cc7-46df-9a04-c11c478de211",
                    "key": "IMG_3535.jpg",
                    "version_id": "f8200dc7-55b6-4785-abd0-f3d13b143c98",
                    "file_id": "e94b243e-9c0c-44df-bd1f-6decc374cf78",
                    "_mimetype": None,
                    "is_head": True,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045933202,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829808184","1375829842808"]',
                    "schema": "public",
                    "table": "files_object",
                    "txId": 533724612,
                    "lsn": 1375829842808,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1688045933693,
                "transaction": None,
            },
            {
                "after": {
                    "created": "2023-06-29T13:00:00",
                    "updated": "2023-06-29T14:00:00",
                    "id": "e94b243e-9c0c-44df-bd1f-6decc374cf78",
                    "uri": "root://eosmedia.cern.ch//eos/media/zenodo/test/data/e9/4b/243e-9c0c-44df-bd1f-6decc374cf78/data",
                    "storage_class": "S",
                    "size": 1562554,
                    "checksum": "md5:3cc016be06f2be46d3a438db23c40bf3",
                    "readable": True,
                    "writable": False,
                    "last_check_at": None,
                    "last_check": True,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045933202,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829808184","1375829859112"]',
                    "schema": "public",
                    "table": "files_files",
                    "txId": 533724612,
                    "lsn": 1375829859112,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1688045933693,
                "transaction": None,
            },
            {
                "after": {
                    "created": "2023-06-29T13:00:00",
                    "updated": "2023-06-29T14:00:00",
                    "id": "0e12b4b6-9cc7-46df-9a04-c11c478de211",
                    "default_location": 1,
                    "default_storage_class": "S",
                    "size": 1562554,
                    "quota_size": 50000000000,
                    "max_file_size": 50000000000,
                    "locked": False,
                    "deleted": False,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045933202,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829808184","1375829875488"]',
                    "schema": "public",
                    "table": "files_bucket",
                    "txId": 533724612,
                    "lsn": 1375829875488,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1688045933693,
                "transaction": None,
            },
        ],
    }
