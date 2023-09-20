# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration oauth actions module."""

from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load
from invenio_rdm_migrator.streams.oauth import (
    OAuthServerClientTransform,
    OAuthServerTokenTransform,
)
from invenio_rdm_migrator.transform import IdentityTransform


class OAuthServerTokenCreateAction(TransformAction):
    """Zenodo to RDM OAuth server create action."""

    name = "oauth-server-token-create"
    load_cls = load.OAuthServerTokenCreateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 2:
            return False

        rules = {
            "oauth2server_client": OperationType.INSERT,
            "oauth2server_token": OperationType.INSERT,
        }

        for op in tx.operations:
            rule = rules.pop(op["source"]["table"], None)
            if not rule or rule != op["op"]:
                return False

        return True

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        client_src = None
        token_src = None

        if self.tx.operations[0]["source"]["table"] == "oauth2server_client":
            client_src = self.tx.operations[0]["after"]
            token_src = self.tx.operations[1]["after"]
        else:  # if it matched the rules there is no other option
            client_src = self.tx.operations[1]["after"]
            token_src = self.tx.operations[0]["after"]

        result = {
            "tx_id": self.tx.id,
            "client": OAuthServerClientTransform()._transform(client_src),
            "token": OAuthServerTokenTransform()._transform(token_src),
        }

        return result


class OAuthServerTokenUpdateAction(TransformAction):
    """Zenodo to RDM OAuth server update action."""

    name = "oauth-server-token-update"
    load_cls = load.OAuthServerTokenUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) == 1:
            # note 1: this action would handle both personal and application tokens
            # note 2: tx with only oauth2server_client are handled by the app action

            op = tx.operations[0]
            return (
                op["source"]["table"] == "oauth2server_token"
                and op["op"] == OperationType.UPDATE
            )

        if len(tx.operations) == 2:
            rules = {
                "oauth2server_client": OperationType.UPDATE,
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
        result = {"tx_id": self.tx.id}

        for op in self.tx.operations:
            if op["source"]["table"] == "oauth2server_client":
                result["client"] = OAuthServerClientTransform()._transform(op["after"])

            elif op["source"]["table"] == "oauth2server_token":
                result["token"] = OAuthServerTokenTransform()._transform(op["after"])

        return result


class OAuthServerTokenDeleteAction(TransformAction):
    """Zenodo to RDM OAuth server delete action."""

    name = "oauth-server-token-delete"
    load_cls = load.OAuthServerTokenDeleteAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "oauth2server_token"
            and op["op"] == OperationType.DELETE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        return {
            "tx_id": self.tx.id,
            "token": OAuthServerTokenTransform()._transform(op["before"]),
        }


class OAuthApplicationCreateAction(TransformAction):
    """Zenodo to RDM OAuth server create action."""

    name = "oauth-application-create"
    load_cls = load.OAuthApplicationCreateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "oauth2server_client"
            and op["op"] == OperationType.INSERT
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        return {
            "tx_id": self.tx.id,
            "client": OAuthServerClientTransform()._transform(op["after"]),
        }


class OAuthApplicationUpdateAction(TransformAction):
    """Zenodo to RDM OAuth server create action."""

    name = "oauth-application-update"
    load_cls = load.OAuthApplicationUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        # note: it will absorb OAuthServerTokenUpdateAction that update only
        # the client (e.g. a name), but the behavior/outcome is left unchanged:
        # an update to oauth2server_client
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "oauth2server_client"
            and op["op"] == OperationType.UPDATE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        return {
            "tx_id": self.tx.id,
            "client": OAuthServerClientTransform()._transform(op["after"]),
        }


class OAuthApplicationDeleteAction(TransformAction):
    """Zenodo to RDM OAuth server create action."""

    name = "oauth-application-delete"
    load_cls = load.OAuthApplicationDeleteAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "oauth2server_client"
            and op["op"] == OperationType.DELETE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        return {
            "tx_id": self.tx.id,
            "client": OAuthServerClientTransform()._transform(op["before"]),
        }


class OAuthLinkedAccountConnectAction(TransformAction):
    """Zenodo to RDM OAuth client linked account connect action."""

    name = "oauth-application-connect"
    load_cls = load.OAuthLinkedAccountConnectAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 4:
            return False

        rules = {
            # OpType is not hashable (to use a dict), the list won't be long in any case
            # so the worst case scenario is not too bad
            "oauthclient_remoteaccount": [OperationType.INSERT, OperationType.UPDATE],
            "oauthclient_remotetoken": [OperationType.INSERT],
            "oauthclient_useridentity": [OperationType.INSERT],
        }

        for op in tx.operations:
            rule = rules.get(op["source"]["table"])
            if not rule:
                return False
            try:
                rule.remove(op["op"])  # prevents double update/insert in sets
            except ValueError:
                return False

        return True

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        remote_account = None
        remote_token = None
        user_identity = None

        for op in self.tx.operations:
            if op["source"]["table"] == "oauthclient_remoteaccount":
                if op["op"] == OperationType.INSERT:
                    remote_account = op["after"]
                else:
                    for key, value in op["after"].items():
                        remote_account[key] = value
            elif op["source"]["table"] == "oauthclient_remotetoken":
                remote_token = op["after"]
            elif op["source"]["table"] == "oauthclient_useridentity":
                user_identity = op["after"]

        return {
            "tx_id": self.tx.id,
            "remote_account": IdentityTransform()._transform(remote_account),
            "remote_token": IdentityTransform()._transform(remote_token),
            "user_identity": IdentityTransform()._transform(user_identity),
        }


class OAuthLinkedAccountDisconnectAction(TransformAction):
    """Zenodo to RDM OAuth client linked account disconnect action."""

    name = "oauth-application-disconnect"
    load_cls = load.OAuthLinkedAccountDisconnectAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) > 3 or len(tx.operations) < 2:
            return False

        rules = {
            "oauthclient_remoteaccount": OperationType.DELETE,
            "oauthclient_remotetoken": OperationType.DELETE,
            "oauthclient_useridentity": OperationType.DELETE,  # optional in gh
        }

        for op in tx.operations:
            rule = rules.pop(op["source"]["table"], None)
            if not rule or rule != op["op"]:
                return False

        # the previous len check means that at this point the rules have 1 or 0 left
        # if the len is 1 then only left should be the identity
        if len(rules) == 1 and not "oauthclient_useridentity" in rules.keys():
            return False

        return True

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        remote_account = None
        remote_token = None
        user_identity = None

        for op in self.tx.operations:
            if op["source"]["table"] == "oauthclient_remoteaccount":
                remote_account = op["before"]
            elif op["source"]["table"] == "oauthclient_remotetoken":
                remote_token = op["before"]
            elif op["source"]["table"] == "oauthclient_useridentity":
                user_identity = op["before"]

        result = {
            "tx_id": self.tx.id,
            "remote_account": IdentityTransform()._transform(remote_account),
            "remote_token": IdentityTransform()._transform(remote_token),
        }

        if user_identity:
            result["user_identity"] = IdentityTransform()._transform(user_identity)

        return result


class OAuthGHDisconnectToken(TransformAction):
    """Zenodo to RDM GH linked account disconnect server token and identity."""

    name = "oauth-gh-application-disconnect"
    load_cls = load.OAuthGHDisconnectToken

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 2:
            return False

        rules = {
            "oauthclient_useridentity": OperationType.DELETE,
            "oauth2server_token": OperationType.DELETE,
        }

        for op in tx.operations:
            rule = rules.pop(op["source"]["table"], None)
            if not rule or rule != op["op"]:
                return False

        return True

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        token = None
        user_identity = None

        for op in self.tx.operations:
            if op["source"]["table"] == "oauth2server_token":
                token = op["before"]
            elif op["source"]["table"] == "oauthclient_useridentity":
                user_identity = op["before"]

        return {
            "tx_id": self.tx.id,
            "token": OAuthServerTokenTransform()._transform(token),
            "user_identity": IdentityTransform()._transform(user_identity),
        }
