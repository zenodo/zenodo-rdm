# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test user actions for RDM migration."""


from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import UserRegistrationAction

from zenodo_rdm_migrator.actions import ZenodoUserRegistrationAction


def test_matches_with_valid_data():
    assert (
        ZenodoUserRegistrationAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.INSERT,
                        "source": {"table": "userprofiles_userprofile"},
                        "after": {},
                    },
                    {
                        "op": OperationType.INSERT,
                        "source": {"table": "accounts_user"},
                        "after": {},
                    },
                ],
            )
        )
        is True
    )


def test_matches_with_invalid_data():
    missing_profile = [
        {"op": OperationType.INSERT, "source": {"table": "accounts_user"}, "after": {}},
    ]

    missing_account = [
        {
            "op": OperationType.INSERT,
            "source": {"table": "userprofiles_userprofile"},
            "after": {},
        }
    ]

    for invalid_ops in [missing_profile, missing_account]:
        assert (
            ZenodoUserRegistrationAction.matches_action(
                Tx(id=1, operations=invalid_ops)
            )
            is False
        )


def test_transform_with_valid_data(register_user_tx):
    action = ZenodoUserRegistrationAction(
        Tx(id=register_user_tx["tx_id"], operations=register_user_tx["operations"])
    )
    assert isinstance(action.transform(), UserRegistrationAction)
