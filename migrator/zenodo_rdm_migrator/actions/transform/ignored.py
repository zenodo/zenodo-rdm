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


class FileChecksumAction(TransformAction):
    """Zenodo to RDM for file checksum."""

    name = "file-checksum"
    load_cls = load.IgnoredAction

    @classmethod
    def matches_action(cls, tx):
        """Checks for a single ."""
        table_ops = [(o["source"]["table"], o["op"]) for o in tx.operations]
        if table_ops == [("files_files", OperationType.UPDATE)]:
            changed_keys = tx.operations[0].get("after", {}).keys()
            return {"last_check", "last_check_at"} < changed_keys
        return False

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        return {}


IGNORED_ACTIONS = [
    FileChecksumAction,
]
