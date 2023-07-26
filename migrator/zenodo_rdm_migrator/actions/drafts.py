# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Migrator is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration drafts row load module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import RDMDraftCreateAction
from invenio_rdm_migrator.transform import IdentityTransform

from ..transform.records import ZenodoRecordTransform


class ZenodoDraftCreateAction(TransformAction):
    """Zenodo to RDM draft creation action."""

    name = "create-zenodo-draft"
    mapped_cls = RDMDraftCreateAction

    def __init__(
        self,
        tx_id,
        data,
        parents_state,
        records_state,
        communities_state,
        pids_state,
    ):
        """Constructor."""
        super().__init__(tx_id=tx_id, data=data)
        # state related
        # FIXME: it is not needed, but there is no easy way to drill them to the
        # RDM action without having a app ctx proxy
        self.parents_state = parents_state
        self.records_state = records_state
        self.communities_state = communities_state
        self.pids_state = pids_state

    def fingerprint(self):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        rules = {
            "pidstore_pid": OperationType.INSERT,  # should we check recid + depid
            "files_bucket": OperationType.INSERT,
            "records_metadata": OperationType.INSERT,
        }

        for operation in self.data:
            table_name = operation["source"]["table"]

            rule = rules.pop(table_name, None)
            if not rule or not rule == operation["op"]:
                return False

        return len(rules) == 0

    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        # draft files should be a separate transaction

        for operation in self.data:
            table_name = operation["source"]["table"]

            if table_name == "pidstore_pid":
                if operation["after"]["pid_type"] == "recid":
                    pid = IdentityTransform()._transform(operation["after"])
            elif table_name == "files_bucket":
                bucket = IdentityTransform()._transform(operation["after"])
            elif table_name == "records_metadata":
                draft_and_parent = ZenodoRecordTransform()._transform(
                    operation["after"]
                )

        return {
            "pid": pid,
            "bucket": bucket,
            "draft": draft_and_parent["draft"],
            "parent": draft_and_parent["parent"],
            # not ideal but the state needs to be passed
            "parents_state": self.parents_state,
            "records_state": self.records_state,
            "communities_state": self.communities_state,
            "pids_state": self.pids_state,
        }
