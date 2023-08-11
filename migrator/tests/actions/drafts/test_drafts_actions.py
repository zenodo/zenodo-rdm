# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions for RDM migration."""


from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from zenodo_rdm_migrator.actions.transform import DraftCreateAction, DraftEditAction


class TestDraftCreateAction:
    """Create draft action tests."""

    def test_matches_with_valid_data(self):
        assert (
            DraftCreateAction.matches_action(
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

    def test_matches_with_invalid_data(self):
        missing_pid = [
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
        ]

        missing_bucket = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "pidstore_pid"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "records_metadata"},
                "after": {},
            },
        ]
        missing_draft = [
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
        ]

        for invalid_ops in [missing_pid, missing_bucket, missing_draft]:
            assert (
                DraftCreateAction.matches_action(Tx(id=1, operations=invalid_ops))
                is False
            )

    def test_transform_with_valid_data(self, create_draft_tx):
        action = DraftCreateAction(
            Tx(id=create_draft_tx["tx_id"], operations=create_draft_tx["operations"])
        )
        assert isinstance(action.transform(), load.DraftCreateAction)


class TestDraftEditAction:
    """Edit/Update draft action tests."""

    def test_matches_with_valid_data(self):
        assert (
            DraftEditAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.UPDATE,
                            "source": {"table": "records_metadata"},
                            "after": {},
                        }
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        other_table = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "files_bucket"},
                "after": {},
            },
        ]

        extra_table = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "pidstore_pid"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "records_metadata"},
                "after": {},
            },
        ]

        insert_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "records_metadata"},
                "after": {},
            },
        ]

        for invalid_ops in [other_table, extra_table, insert_op]:
            assert (
                DraftEditAction.matches_action(Tx(id=1, operations=invalid_ops))
                is False
            )

    def test_transform_with_valid_data(self, update_draft_tx):
        action = DraftEditAction(
            Tx(id=update_draft_tx["tx_id"], operations=update_draft_tx["operations"])
        )
        assert isinstance(action.transform(), load.DraftEditAction)
