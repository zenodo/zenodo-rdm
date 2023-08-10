# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Migrator is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration users actions module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from ...transform.entries.users import ZenodoUserEntry


class UserRegistrationAction(TransformAction):
    """Zenodo to RDM user registration action."""

    name = "register-user"
    load_cls = load.UserRegistrationAction

    @classmethod
    def matches_action(cls, tx):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        rules = {
            "userprofiles_userprofile": OperationType.INSERT,
            "accounts_user": OperationType.INSERT,
        }

        for operation in tx.operations:
            table_name = operation["source"]["table"]

            rule = rules.pop(table_name, None)
            # no duplicated tables, can fail fast if rule is None
            if not rule or not rule == operation["op"]:
                return False

        return len(rules) == 0

    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        payload = {}
        for operation in self.tx.operations:
            payload = {**payload, **operation["after"]}

        # it comes in milliseonds
        ts = self.tx.operations[0]["source"]["ts_ms"]
        payload["created"] = ts
        payload["updated"] = ts

        user = ZenodoUserEntry().transform(payload)
        self._microseconds_to_isodate(data=user, fields=["confirmed_at"])
        self._milliseconds_to_isodate(data=user, fields=["created", "updated"])

        login_info = user.pop("login_information")
        self._microseconds_to_isodate(
            data=login_info, fields=["last_login_at", "current_login_at"]
        )

        return dict(tx_id=self.tx.id, user=user, login_information=login_info)


class UserEditAction(TransformAction):
    """Zenodo to RDM user edit action."""

    name = "edit-user"
    load_cls = load.UserEditAction

    @classmethod
    def matches_action(cls, tx):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        # all operations are updates on the user table
        # in some cases (e.g. user confirmation there are two due to the login information)
        for operation in tx.operations:
            if (
                not "accounts_user" == operation["source"]["table"]
                or not operation["op"] == OperationType.UPDATE
            ):
                return False

        return len(tx.operations) >= 1  # there was at least one matching op

    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        # use only the latest updated information
        payload = {**self.tx.operations[-1]["after"]}

        # should be already in microseconds
        ts = self.tx.operations[0]["source"]["ts_ms"]
        payload["created"] = ts
        payload["updated"] = ts

        user = ZenodoUserEntry().transform(payload)
        self._microseconds_to_isodate(data=user, fields=["confirmed_at"])
        self._milliseconds_to_isodate(data=user, fields=["created", "updated"])

        login_info = user.pop("login_information")
        self._microseconds_to_isodate(
            data=login_info, fields=["last_login_at", "current_login_at"]
        )
        return dict(tx_id=self.tx.id, user=user, login_information=login_info)


class UserDeactivationAction(TransformAction):
    """Zenodo to RDM user deactivation action."""

    name = "deactivate-user"
    load_cls = load.UserDeactivationAction

    @classmethod
    def matches_action(cls, tx):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        # one update on the account_user and multiple session deletes
        account_seen = False
        for operation in tx.operations:
            if "accounts_user" == operation["source"]["table"]:
                update_not_active = (
                    operation["after"]["active"]
                    or not operation["op"] == OperationType.UPDATE
                )
                if update_not_active or account_seen:
                    return False

                account_seen = True

            elif "accounts_user_session_activity" == operation["source"]["table"]:
                if not operation["op"] == OperationType.DELETE:
                    return False
            else:
                return False

        return True

    # TODO
    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        user = None
        sessions = []
        ts = self.tx.operations[0]["source"]["ts_ms"]
        for operation in self.tx.operations:
            if "accounts_user" == operation["source"]["table"]:
                operation["after"]["created"] = ts
                operation["after"]["updated"] = ts
                user = ZenodoUserEntry().transform(operation["after"])

                self._microseconds_to_isodate(data=user, fields=["confirmed_at"])
                self._milliseconds_to_isodate(data=user, fields=["created", "updated"])
            else:  # can only be a session as per match function
                # important: the data comes in "before"
                session_data = operation["before"]
                self._microseconds_to_isodate(
                    data=session_data, fields=["created", "updated"]
                )
                sessions.append(session_data)

        # cannot guarantee user will be the first of the previous loop
        for session in sessions:
            session["user_id"] = user["id"]

        login_info = user.pop("login_information")
        self._microseconds_to_isodate(
            data=login_info, fields=["last_login_at", "current_login_at"]
        )
        return dict(
            tx_id=self.tx.id, user=user, login_information=login_info, sessions=sessions
        )
