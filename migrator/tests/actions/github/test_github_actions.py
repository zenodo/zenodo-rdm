# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test GitHub actions for RDM migration."""

from pathlib import Path

import orjson
import pytest
from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from zenodo_rdm_migrator.actions.transform import (
    HookEventCreateAction,
    HookEventUpdateAction,
    HookRepoUpdateAction,
)

##
# TOKENS
##


@pytest.fixture()
def hook_enable_step1_tx():
    """Transaction enable a hook.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "hook_enable_step1.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestHookRepoUpdateAction:
    """Create OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        assert (
            HookRepoUpdateAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.UPDATE,
                            "source": {"table": "github_repositories"},
                            "after": {},
                        },
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "github_repositories"},
                "after": {},
            },
        ]

        extra_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "github_repositories"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        for invalid_ops in [
            empty,
            wrong_op,
            extra_op,
        ]:
            assert (
                HookRepoUpdateAction.matches_action(Tx(id=1, operations=invalid_ops))
                is False
            )

    def test_transform_with_valid_data(self, hook_enable_step1_tx):
        action = HookRepoUpdateAction(
            Tx(
                id=hook_enable_step1_tx["tx_id"],
                operations=hook_enable_step1_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.HookRepoUpdateAction)


@pytest.fixture()
def hook_enable_step2_tx():
    """Transaction enable a hook.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "hook_enable_step2.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestHookEventCreateAction:
    """Create OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        with_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "webhooks_events"},
                "after": {},
            },
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            },
        ]
        without_token = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "webhooks_events"},
                "after": {},
            }
        ]
        for valid_ops in [
            with_token,
            without_token,
        ]:
            assert (
                HookEventCreateAction.matches_action(Tx(id=1, operations=valid_ops))
                is True
            )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "webhooks_events"},
                "after": {},
            }
        ]

        extra_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "webhooks_events"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]
        only_token = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "oauth2server_token"},
                "after": {},
            }
        ]

        for invalid_ops in [
            empty,
            wrong_op,
            extra_op,
            only_token,
        ]:
            assert (
                HookEventCreateAction.matches_action(Tx(id=1, operations=invalid_ops))
                is False
            )

    def test_transform_with_valid_data(self, hook_enable_step2_tx):
        action = HookEventCreateAction(
            Tx(
                id=hook_enable_step2_tx["tx_id"],
                operations=hook_enable_step2_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.HookEventCreateAction)


@pytest.fixture()
def hook_disable_tx():
    """Transaction disable a hook.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "hook_disable.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


@pytest.fixture()
def hook_update_tx():
    """Transaction update a hook.

    As it would be after the extraction step.
    """
    datafile = Path(__file__).parent / "testdata" / "hook_update.jsonl"
    with open(datafile, "rb") as reader:
        ops = [orjson.loads(line)["value"] for line in reader]

    return {"tx_id": 1, "operations": ops}


class TestHookEventUpdateAction:
    """Create OAuth server token action tests."""

    def test_matches_with_valid_data(self):
        assert (
            HookEventUpdateAction.matches_action(
                Tx(
                    id=1,
                    operations=[
                        {
                            "op": OperationType.UPDATE,
                            "source": {"table": "webhooks_events"},
                            "after": {},
                        },
                    ],
                )
            )
            is True
        )

    def test_matches_with_invalid_data(self):
        empty = []

        wrong_op = [
            {
                "op": OperationType.INSERT,
                "source": {"table": "webhooks_events"},
                "after": {},
            }
        ]

        extra_op = [
            {
                "op": OperationType.UPDATE,
                "source": {"table": "webhooks_events"},
                "after": {},
            },
            {"op": OperationType.INSERT, "source": {"table": "another"}, "after": {}},
        ]

        for invalid_ops in [
            empty,
            wrong_op,
            extra_op,
        ]:
            assert (
                HookEventUpdateAction.matches_action(Tx(id=1, operations=invalid_ops))
                is False
            )

    def test_transform_with_valid_data_disable(self, hook_disable_tx):
        action = HookEventUpdateAction(
            Tx(
                id=hook_disable_tx["tx_id"],
                operations=hook_disable_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.HookEventUpdateAction)

    def test_transform_with_valid_data_update(self, hook_update_tx):
        action = HookEventUpdateAction(
            Tx(
                id=hook_update_tx["tx_id"],
                operations=hook_update_tx["operations"],
            )
        )
        assert isinstance(action.transform(), load.HookEventUpdateAction)
