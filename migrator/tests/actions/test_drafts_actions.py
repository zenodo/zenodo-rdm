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


def test_transform_with_valid_data(create_draft_tx):
    action = ZenodoDraftCreateAction(
        tx_id=create_draft_tx["tx_id"],
        data=create_draft_tx["operations"],
        parents_state={},
        records_state={},
        communities_state={},
        pids_state={},
    )

    assert isinstance(action.transform(), RDMDraftCreateAction)
