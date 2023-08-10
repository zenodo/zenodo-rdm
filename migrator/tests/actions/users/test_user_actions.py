# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test user actions for RDM migration."""


from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from zenodo_rdm_migrator.actions.transform import (
    UserDeactivationAction,
    UserEditAction,
    UserRegistrationAction,
)

###
# USER REGISTRATION
###


def test_user_registration_matches_with_valid_data():
    assert (
        UserRegistrationAction.matches_action(
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


def test_user_registration_matches_with_invalid_data():
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
            UserRegistrationAction.matches_action(Tx(id=1, operations=invalid_ops))
            is False
        )


def test_user_registration_transform_with_valid_data(
    secret_keys_state, register_user_tx
):
    action = UserRegistrationAction(
        Tx(id=register_user_tx["tx_id"], operations=register_user_tx["operations"])
    )
    assert isinstance(action.transform(), load.UserRegistrationAction)


###
# USER EDIT
###


def test_user_edit_matches_with_one_op():
    assert (
        UserEditAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.UPDATE,
                        "source": {"table": "accounts_user"},
                        "after": {},
                    },
                ],
            )
        )
        is True
    )


def test_user_edit_matches_with_multiple_ops():
    assert (
        UserEditAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.UPDATE,
                        "source": {"table": "accounts_user"},
                        "after": {},
                    },
                    {
                        "op": OperationType.UPDATE,
                        "source": {"table": "accounts_user"},
                        "after": {},
                    },
                ],
            )
        )
        is True
    )


def test_user_edit_matches_with_invalid_data():
    not_update = [
        {"op": OperationType.INSERT, "source": {"table": "accounts_user"}, "after": {}},
    ]

    not_account = [
        {"op": OperationType.UPDATE, "source": {"table": "another"}, "after": {}},
    ]

    one_not_account = [
        {"op": OperationType.UPDATE, "source": {"table": "accounts_user"}, "after": {}},
        {"op": OperationType.UPDATE, "source": {"table": "another"}, "after": {}},
    ]

    for invalid_ops in [not_update, not_account, one_not_account]:
        assert UserEditAction.matches_action(Tx(id=1, operations=invalid_ops)) is False


def test_user_edit_transform_with_valid_data(
    secret_keys_state, login_user_tx, confirm_user_tx
):
    for tx in [login_user_tx, confirm_user_tx]:
        action = UserEditAction(Tx(id=tx["tx_id"], operations=tx["operations"]))
        assert isinstance(action.transform(), load.UserEditAction)


###
# USER DEACTIVATION
###
def test_user_deactivation_matches_with_one_user():
    assert (
        UserDeactivationAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.UPDATE,
                        "source": {"table": "accounts_user"},
                        "after": {"active": False},
                    },
                ],
            )
        )
        is True
    )


def test_user_deactivation_matches_with_one_session():
    assert (
        UserDeactivationAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.UPDATE,
                        "source": {"table": "accounts_user"},
                        "after": {"active": False},
                    },
                    {
                        "op": OperationType.DELETE,
                        "source": {"table": "accounts_user_session_activity"},
                        "after": {},
                    },
                ],
            )
        )
        is True
    )


def test_user_deactivation_matches_with_multiple_session():
    assert (
        UserDeactivationAction.matches_action(
            Tx(
                id=1,
                operations=[
                    {
                        "op": OperationType.UPDATE,
                        "source": {"table": "accounts_user"},
                        "after": {"active": False},
                    },
                    {
                        "op": OperationType.DELETE,
                        "source": {"table": "accounts_user_session_activity"},
                        "after": {},
                    },
                    {
                        "op": OperationType.DELETE,
                        "source": {"table": "accounts_user_session_activity"},
                        "after": {},
                    },
                ],
            )
        )
        is True
    )


def test_user_deactivation_matches_with_invalid_data():
    not_update = [
        {
            "op": OperationType.INSERT,
            "source": {"table": "accounts_user"},
            "after": {"active": False},
        },
    ]

    still_active = [
        {
            "op": OperationType.INSERT,
            "source": {"table": "accounts_user"},
            "after": {"active": True},
        },
    ]

    not_account = [
        {"op": OperationType.UPDATE, "source": {"table": "another"}, "after": {}},
    ]

    account_no_session = [
        {
            "op": OperationType.UPDATE,
            "source": {"table": "accounts_user"},
            "after": {"active": False},
        },
        {"op": OperationType.DELETE, "source": {"table": "another"}, "after": {}},
    ]

    session_no_account = [
        {
            "op": OperationType.DELETE,
            "source": {"table": "accounts_user_session_activity"},
            "after": {},
        },
        {"op": OperationType.UPDATE, "source": {"table": "another"}, "after": {}},
    ]

    session_not_update = [
        {
            "op": OperationType.UPDATE,
            "source": {"table": "accounts_user"},
            "after": {"active": False},
        },
        {
            "op": OperationType.UPDATE,
            "source": {"table": "accounts_user_session_activity"},
            "after": {},
        },
    ]

    extra_table = [
        {
            "op": OperationType.UPDATE,
            "source": {"table": "accounts_user"},
            "after": {"active": False},
        },
        {
            "op": OperationType.DELETE,
            "source": {"table": "accounts_user_session_activity"},
            "after": {},
        },
        {"op": OperationType.UPDATE, "source": {"table": "another"}, "after": {}},
    ]

    for invalid_ops in [
        not_update,
        still_active,
        not_account,
        account_no_session,
        session_no_account,
        session_not_update,
        extra_table,
    ]:
        assert (
            UserDeactivationAction.matches_action(Tx(id=1, operations=invalid_ops))
            is False
        )


def test_user_edit_transform_with_valid_data(secret_keys_state, user_deactivation_tx):
    action = UserDeactivationAction(
        Tx(
            id=user_deactivation_tx["tx_id"],
            operations=user_deactivation_tx["operations"],
        )
    )
    assert isinstance(action.transform(), load.UserDeactivationAction)
