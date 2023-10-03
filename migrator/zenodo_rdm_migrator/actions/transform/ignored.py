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

from zenodo_rdm_migrator.transform.records import ZENODO_DATACITE_PREFIXES


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
        if tx.as_ops_tuples() == [("files_files", OperationType.UPDATE)]:
            _, file = tx.ops_by("files_files").popitem()
            changed_keys = file.keys() - {"id"}
            return {"last_check", "last_check_at", "updated"} <= changed_keys
        return False


class UserSessionAction(IgnoredTransformAction):
    """Zenodo to RDM for user session."""

    name = "user-session"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a user login."""
        ops = tx.as_ops_tuples()
        user_update_ops = tx.as_ops_tuples(
            include=["accounts_user"],
            op_types=[OperationType.UPDATE],
        )
        session_activity_ops = tx.as_ops_tuples(
            include=["accounts_user_session_activity"],
        )
        # Don't accidentally match user deactivations
        if len(user_update_ops) == 1:
            _, user = tx.ops_by("accounts_user").popitem()
            if user.get("active") is False:
                return False
        # there might be one optional user update + multiple session_activirty ops
        return (
            len(ops) == len(user_update_ops + session_activity_ops)
            and len(session_activity_ops) >= 1
        )


class GitHubSyncAction(IgnoredTransformAction):
    """Zenodo to RDM for GitHub sync."""

    name = "gh-sync"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single OAuth client remote account update op."""
        return tx.as_ops_tuples() == [
            ("oauthclient_remoteaccount", OperationType.UPDATE)
        ]


class GitHubPingAction(IgnoredTransformAction):
    """Zenodo to RDM for GitHub sync."""

    name = "gh-ping"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single GitHub repo update to the `ping` column."""
        if tx.as_ops_tuples() == [("github_repositories", OperationType.UPDATE)]:
            repo = tx.ops_by("github_repositories")
            changed_keys = repo.keys() - {"id"}
            return {"ping", "updated"} == changed_keys
        return False


class OAuthReLoginAction(IgnoredTransformAction):
    """Zenodo to RDM for OAuth re-login."""

    name = "oauth-relogin"

    @classmethod
    def matches_action(cls, tx):
        """Checks for an OAuth login."""
        return tx.as_ops_tuples() == [
            ("accounts_user", OperationType.UPDATE),
            ("oauthclient_remotetoken", OperationType.UPDATE),
        ]


class DataCiteDOIRegistration(IgnoredTransformAction):
    """Zenodo DataCite DOI registration."""

    name = "doi-registration"

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single Zenodo DOI update to registered status."""
        ops = tx.as_ops_tuples()
        new_version = [("pidstore_pid", OperationType.UPDATE)]
        first_publish = [
            ("pidstore_pid", OperationType.UPDATE),
            ("pidstore_pid", OperationType.UPDATE),
        ]
        if ops in (new_version, first_publish):
            pids = tx.ops_by("pidstore_pid", group_key=("pid_type", "pid_value"))
            return all(
                pid["pid_type"] == "doi"
                and pid["pid_value"].startswith(ZENODO_DATACITE_PREFIXES)
                and pid["status"] == "R"
                for pid in pids.values()
            )


IGNORED_ACTIONS = [
    FileChecksumAction,
    UserSessionAction,
    GitHubSyncAction,
    GitHubPingAction,
    OAuthReLoginAction,
    DataCiteDOIRegistration,
]
