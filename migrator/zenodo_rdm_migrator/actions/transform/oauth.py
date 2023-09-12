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
