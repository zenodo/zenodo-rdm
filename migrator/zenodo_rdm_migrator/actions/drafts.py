# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Migrator is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration drafts actions module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import (
    DraftCreateAction as LoadDraftCreateAction,
)
from invenio_rdm_migrator.transform import IdentityTransform, JSONTransformMixin

from ..transform.records import ZenodoRecordTransform


class DraftCreateAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM draft creation action."""

    name = "create-zenodo-draft"
    load_cls = LoadDraftCreateAction

    @classmethod
    def matches_action(cls, tx):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        rules = {
            "pidstore_pid": OperationType.INSERT,
            "files_bucket": OperationType.INSERT,
            "records_metadata": OperationType.INSERT,
        }

        for operation in tx.operations:
            table_name = operation["source"]["table"]

            rule = rules.pop(table_name, None)
            # rule can be None, e.g. draft creation has two rows on pidstore_pid
            # one for recid and one for depid. the second one should be ignored.
            # FIXME: should we check pid_types
            if rule and not rule == operation["op"]:
                return False

        return len(rules) == 0

    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        # draft files should be a separate transaction
        for operation in self.tx.operations:
            table_name = operation["source"]["table"]

            if table_name == "pidstore_pid":
                if operation["after"]["pid_type"] == "recid":
                    pid = IdentityTransform()._transform(operation["after"])
            elif table_name == "files_bucket":
                bucket = IdentityTransform()._transform(operation["after"])
            elif table_name == "records_metadata":
                # need to json load the draft json
                # the parent json is calculated on transform
                self._load_json_fields(data=operation["after"], fields=["json"])
                draft_and_parent = ZenodoRecordTransform()._transform(
                    operation["after"]
                )

        return dict(
            tx_id=self.tx.id,
            pid=pid,
            bucket=bucket,
            draft=draft_and_parent["draft"],
            parent=draft_and_parent["parent"],
        )
