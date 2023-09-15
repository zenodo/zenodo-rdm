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
from invenio_rdm_migrator.streams.oauth import OAuthServerTokenTransform
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
            "client": IdentityTransform()._transform(client_src),
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
                result["client"] = IdentityTransform()._transform(op["after"])

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
            "client": IdentityTransform()._transform(op["after"]),
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
            "client": IdentityTransform()._transform(op["after"]),
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
            "client": IdentityTransform()._transform(op["before"]),
        }
