# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions for RDM migration."""


from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import DraftCreateAction

from zenodo_rdm_migrator.actions import ZenodoDraftCreateAction


def test_matches_with_valid_data():
    assert (
        ZenodoDraftCreateAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.INSERT,
                        "source": {"table": "pidstore_pid"},
                        "after": {},
                    },
                    {
                        "op": OperationType.INSERT,
                        "source": {"table": "files_bucket"},
                        "after": {},
                    },
                    {
                        "op": OperationType.INSERT,
                        "source": {"table": "records_metadata"},
                        "after": {},
                    },
                ],
            )
        )
        is True
    )


def test_matches_with_invalid_data():
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

    for invalid_ops in [missing_pid, missing_bucket, missing_draft]:
        assert (
            ZenodoDraftCreateAction.matches_action(Tx(id=1, operations=invalid_ops))
            is False
        )


def test_transform_with_valid_data(create_draft_tx):
    action = ZenodoDraftCreateAction(
        Tx(id=create_draft_tx["tx_id"], operations=create_draft_tx["operations"])
    )
    assert isinstance(action.transform(), DraftCreateAction)
