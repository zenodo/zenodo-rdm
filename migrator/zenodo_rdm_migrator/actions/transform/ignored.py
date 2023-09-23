# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Migrator is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM migration ignored actions module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load


class IgnoredTransformAction(TransformAction):
    """Transform ignored actions."""

    load_cls = load.IgnoredAction

    def _transform_data(self):
        """Return nothing."""
        return {}


class FileChecksumAction(IgnoredTransformAction):
    """Zenodo to RDM for file checksum."""

    name = "file-checksum"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single file instance update."""
        table_ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        if table_ops == [("files_files", OperationType.UPDATE)]:
            changed_keys = tx.operations[0].get("after", {}).keys()
            return {"last_check", "last_check_at"} < changed_keys
        return False


class UserSessionAction(IgnoredTransformAction):
    """Zenodo to RDM for user session."""

    name = "user-session"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        table_ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        return all(t == "accounts_user_session_activity" for t, _ in table_ops)


class GitHubSyncAction(IgnoredTransformAction):
    """Zenodo to RDM for GitHub sync."""

    name = "gh-sync"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        table_ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        return table_ops == [("oauthclient_remoteaccount", OperationType.UPDATE)]


class OAuthReLoginAction(IgnoredTransformAction):
    """Zenodo to RDM for OAuth re-login."""

    name = "oauth-relogin"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        table_ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        return table_ops == [
            ("accounts_user", OperationType.UPDATE),
            ("oauthclient_remotetoken", OperationType.UPDATE),
        ]


IGNORED_ACTIONS = [
    FileChecksumAction,
    UserSessionAction,
    GitHubSyncAction,
    OAuthReLoginAction,
]
