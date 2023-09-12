# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test OAuth actions for RDM migration."""

from pathlib import Path

import orjson
import pytest
from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from zenodo_rdm_migrator.actions.transform import OAuthServerTokenCreateAction


@pytest.fixture()
def create_oauth_server_token_tx(tx_files):
    """Transaction data to create an OAuth server token.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "create.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestOAuthServerTokenCreateAction:
    """Create OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        assert (
            OAuthServerTokenCreateAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.INSERT,
                            "source": {"table": "oauth2server_client"},
                            "after": {},
                        },
                        {
                            "op": OperationType.INSERT,
                            "source": {"table": "oauth2server_token"},
                            "after": {},
                        },
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        missing_client = [
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        missing_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        only_client = [
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}}
        ]

        only_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            }
        ]

        wrong_op_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        wrong_op_client = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_client"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "another"},
                "after": {},
            },
            {
                "op": OperationType.INSERT,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        for invalid_ops in [
            missing_client,
            missing_token,
            wrong_op_client,
            wrong_op_token,
            extra_op,
        ]:
            assert (
                OAuthServerTokenCreateAction.matches_action(
                    Tx(id=1, operations=invalid_ops)
                )
                is False
            )

    def test_transform_with_valid_data(self, create_oauth_server_token_tx):
        action = OAuthServerTokenCreateAction(
            Tx(
                id=create_oauth_server_token_tx["tx_id"],
                operations=create_oauth_server_token_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.OAuthServerTokenCreateAction)
