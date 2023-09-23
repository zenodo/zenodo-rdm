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
        ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        if ops == [("files_files", OperationType.UPDATE)]:
            changed_keys = tx.operations[0].get("after", {}).keys() - {"id"}
            return {"last_check", "last_check_at", "updated"} == changed_keys
        return False


class UserSessionAction(IgnoredTransformAction):
    """Zenodo to RDM for user session."""

    name = "user-session"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        user_updates = [o for o in ops if o == ("accounts_user", OperationType.UPDATE)]
        session_activity_ops = [
            o for o in ops if o[0] == "accounts_user_session_activity"
        ]
        # Don't accidentally match user deactivations
        if len(user_updates) == 1:
            if tx.operations[0].get("after", {}).get("active") is False:
                return False
        # there might be one optional user update + multiple session_activirty ops
        return (
            len(ops) == len(user_updates + session_activity_ops)
            and len(session_activity_ops) > 1
        )


class GitHubSyncAction(IgnoredTransformAction):
    """Zenodo to RDM for GitHub sync."""

    name = "gh-sync"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        return ops == [("oauthclient_remoteaccount", OperationType.UPDATE)]


class GitHubPingAction(IgnoredTransformAction):
    """Zenodo to RDM for GitHub sync."""

    name = "gh-ping"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        if ops == [("github_repositories", OperationType.UPDATE)]:
            changed_keys = tx.operations[0].get("after", {}).keys() - {"id"}
            return {"ping", "updated"} == changed_keys
        return False


class OAuthReLoginAction(IgnoredTransformAction):
    """Zenodo to RDM for OAuth re-login."""

    name = "oauth-relogin"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        return ops == [
            ("accounts_user", OperationType.UPDATE),
            ("oauthclient_remotetoken", OperationType.UPDATE),
        ]


IGNORED_ACTIONS = [
    FileChecksumAction,
    UserSessionAction,
    GitHubSyncAction,
    GitHubPingAction,
    OAuthReLoginAction,
]
