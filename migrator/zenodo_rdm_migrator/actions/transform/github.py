# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration github actions module."""

from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load
from invenio_rdm_migrator.streams.github import GitHubRepositoryTransform
from invenio_rdm_migrator.streams.oauth import OAuthServerTokenTransform
from invenio_rdm_migrator.transform import IdentityTransform


class HookRepoUpdateAction(TransformAction):
    """Zenodo to RDM GitHub repository update of a webhook.

    This will serve for hook enabling first phase and for disabling, as well as for
    normal repository updates.
    """

    name = "gh-hook-repo-update"
    load_cls = load.HookRepoUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "github_repositories"
            and op["op"] == OperationType.UPDATE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        result = {
            "tx_id": self.tx.id,
            "gh_repository": GitHubRepositoryTransform()._transform(op["after"]),
        }

        return result


class HookEventCreateAction(TransformAction):
    """Zenodo to RDM webhook create action.

    This will serve for hook enabling first phase and for disabling, as well as for
    normal repository updates.
    """

    name = "gh-hook-event-create"
    load_cls = load.HookEventCreateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) == 1:
            op = tx.operations[0]
            return (
                op["source"]["table"] == "webhooks_events"
                and op["op"] == OperationType.INSERT
            )

        if len(tx.operations) == 2:
            rules = {
                "webhooks_events": OperationType.INSERT,
                "oauth2server_token": OperationType.UPDATE,
            }

            for op in tx.operations:
                rule = rules.pop(op["source"]["table"], None)
                if not rule or rule != op["op"]:
                    return False

            return True

        return False

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        webhook_event = None
        server_token = None
        for op in self.tx.operations:
            if op["source"]["table"] == "webhooks_events":
                webhook_event = op["after"]
            elif op["source"]["table"] == "oauth2server_token":
                server_token = op["after"]

        result = {
            "tx_id": self.tx.id,
            "webhook_event": IdentityTransform()._transform(webhook_event),
        }
        if server_token:
            result["oauth_token"] = OAuthServerTokenTransform()._transform(server_token)

        return result


class HookEventUpdateAction(TransformAction):
    """Zenodo to RDM webhook event update."""

    name = "gh-hook-event-update"
    load_cls = load.HookEventUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "webhooks_events"
            and op["op"] == OperationType.UPDATE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        result = {
            "tx_id": self.tx.id,
            "webhook_event": IdentityTransform()._transform(op["after"]),
        }

        return result
