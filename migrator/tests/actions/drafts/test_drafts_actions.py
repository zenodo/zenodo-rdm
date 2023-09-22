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

from zenodo_rdm_migrator.actions.transform.drafts import (
    DraftCreateAction,
    DraftEditAction,
    DraftPublishAction,
)


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

    def test_transform_with_valid_data(self, state, create_draft_tx):
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


class TestDraftPublishAction:
    """Publish draft action tests."""

    def test_matches_with_valid_data(self):
        assert (
            DraftPublishAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {  # draft
                            "source": {"table": "pidstore_pid"},
                            "op": OperationType.UPDATE,
                            "after": {"pid_type": "recid", "id": 1, "status": "K"},
                        },
                        {  # draft
                            "source": {"table": "pidstore_pid"},
                            "op": OperationType.UPDATE,
                            "after": {"pid_type": "recid", "id": 1, "status": "R"},
                        },
                        {  # parent
                            "source": {"table": "pidstore_pid"},
                            "op": OperationType.UPDATE,
                            "after": {"pid_type": "recid", "id": 2, "status": "R"},
                        },
                        {  # draft
                            "source": {"table": "pidstore_pid"},
                            "op": OperationType.UPDATE,
                            "after": {"pid_type": "recid", "id": 1, "status": "R"},
                        },
                        {  # parent
                            "source": {"table": "pidstore_pid"},
                            "op": OperationType.UPDATE,
                            "after": {"pid_type": "recid", "id": 2, "status": "M"},
                        },
                        {
                            "source": {"table": "pidstore_redirect"},
                            "op": OperationType.INSERT,
                        },
                        {
                            "source": {"table": "pidrelations_pidrelation"},
                            "op": OperationType.DELETE,
                        },
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        missing_pidrel = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
        ]

        missing_pidredirect = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        missing_one_draft = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        missing_one_parent = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        wrong_draft_status = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        wrong_parent_status = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        no_draft = [
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        no_parent = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        wrong_op_type_draft = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.INSERT,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        wrong_op_type_parent = [
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "K"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.INSERT,
                "after": {"pid_type": "recid", "id": 2, "status": "R"},
            },
            {  # draft
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 1, "status": "R"},
            },
            {  # parent
                "source": {"table": "pidstore_pid"},
                "op": OperationType.UPDATE,
                "after": {"pid_type": "recid", "id": 2, "status": "M"},
            },
            {"source": {"table": "pidstore_redirect"}, "op": OperationType.INSERT},
            {
                "source": {"table": "pidrelations_pidrelation"},
                "op": OperationType.DELETE,
            },
        ]

        for invalid_ops in [
            missing_pidredirect,
            missing_pidrel,
            missing_one_draft,
            missing_one_parent,
            wrong_parent_status,
            wrong_draft_status,
            no_draft,
            no_parent,
            wrong_op_type_draft,
            wrong_op_type_parent,
        ]:
            assert (
                DraftPublishAction.matches_action(Tx(id=1, operations=invalid_ops))
                is False
            )

    def test_transform_with_valid_data(self, draft_publish_tx):
        action = DraftPublishAction(
            Tx(id=draft_publish_tx["tx_id"], operations=draft_publish_tx["operations"])
        )
        assert isinstance(action.transform(), load.DraftPublishAction)
