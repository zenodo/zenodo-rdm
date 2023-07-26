# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions for RDM migration."""


from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import RDMDraftCreateAction

from zenodo_rdm_migrator.actions import ZenodoDraftCreateAction


def test_fingerprint_with_valid_data():
    data = [
        {"op": OperationType.INSERT, "source": {"table": "pidstore_pid"}, "after": {}},
        {"op": OperationType.INSERT, "source": {"table": "files_bucket"}, "after": {}},
        {
            "op": OperationType.INSERT,
            "source": {"table": "records_metadata"},
            "after": {},
        },
    ]
    action = ZenodoDraftCreateAction(
        tx_id=1,
        data=data,
        parents_state={},
        records_state={},
        communities_state={},
        pids_state={},
    )
    assert action.fingerprint() is True


def test_fingerprint_with_invalid_data():
    missing_pid = [
        {"op": OperationType.INSERT, "source": {"table": "files_bucket"}, "after": {}},
        {
            "op": OperationType.INSERT,
            "source": {"table": "records_metadata"},
            "after": {},
        },
    ]

    missing_bucket = [
        {"op": OperationType.INSERT, "source": {"table": "pidstore_pid"}, "after": {}},
        {
            "op": OperationType.INSERT,
            "source": {"table": "records_metadata"},
            "after": {},
        },
    ]
    missing_draft = [
        {"op": OperationType.INSERT, "source": {"table": "pidstore_pid"}, "after": {}},
        {"op": OperationType.INSERT, "source": {"table": "files_bucket"}, "after": {}},
    ]

    for invalid in [missing_pid, missing_bucket, missing_draft]:
        action = ZenodoDraftCreateAction(
            tx_id=1,
            data=invalid,
            parents_state={},
            records_state={},
            communities_state={},
            pids_state={},
        )
        assert action.fingerprint() is False


def test_transform_with_valid_data():
    tx_data = {
        "tx_id": 533724568,
        "operations": [
            {
                "after": {
                    "created": 1688045928842023,
                    "updated": 1688045928842033,
                    "id": 12132090,
                    "pid_type": "recid",
                    "pid_value": "1217215",
                    "pid_provider": None,
                    "status": "K",
                    "object_type": None,
                    "object_uuid": None,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045929011,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829693272","1375829710016"]',
                    "schema": "public",
                    "table": "pidstore_pid",
                    "txId": 533724568,
                    "lsn": 1375829710016,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
                "ts_ms": 1688045929132,
                "transaction": None,
            },
            {
                "after": {
                    "created": 1688045928845041,
                    "updated": 1688045928845050,
                    "id": 12132091,
                    "pid_type": "depid",
                    "pid_value": "1217215",
                    "pid_provider": None,
                    "status": "R",
                    "object_type": "rec",
                    "object_uuid": "b7547ab1-47d2-48e2-9867-ca597b4ebb41",
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045929011,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829693272","1375829710456"]',
                    "schema": "public",
                    "table": "pidstore_pid",
                    "txId": 533724568,
                    "lsn": 1375829710456,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
                "ts_ms": 1688045929132,
                "transaction": None,
            },
            {
                "after": {
                    "created": 1688045928885348,
                    "updated": 1688045928885363,
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
                    "ts_ms": 1688045929011,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829693272","1375829718624"]',
                    "schema": "public",
                    "table": "files_bucket",
                    "txId": 533724568,
                    "lsn": 1375829718624,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
                "ts_ms": 1688045929132,
                "transaction": None,
            },
            {
                "after": {
                    "created": 1688045928906896,
                    "updated": 1688045928906905,
                    "id": "b7547ab1-47d2-48e2-9867-ca597b4ebb41",
                    # it assumes the json field comes as a dict not a string
                    "json": {
                        "recid": 1217215,
                        "$schema": "https://zenodo.org/schemas/deposits/records/record-v1.0.0.json",
                        "_buckets": {"deposit": "0e12b4b6-9cc7-46df-9a04-c11c478de211"},
                        "_deposit": {
                            "id": "1217215",
                            "owners": [86261],
                            "status": "draft",
                            "created_by": 86261,
                        },
                        "conceptrecid": "1217214",
                    },
                    "version_id": 1,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1688045929011,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1375829693272","1375829740696"]',
                    "schema": "public",
                    "table": "records_metadata",
                    "txId": 533724568,
                    "lsn": 1375829740696,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
                "ts_ms": 1688045929132,
                "transaction": None,
            },
        ],
    }

    action = ZenodoDraftCreateAction(
        tx_id=tx_data["tx_id"],
        data=tx_data["operations"],
        parents_state={},
        records_state={},
        communities_state={},
        pids_state={},
    )

    assert isinstance(action.transform(), RDMDraftCreateAction)
