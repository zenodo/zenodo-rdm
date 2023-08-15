# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Migrator is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration drafts actions module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.ids import generate_recid
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load
from invenio_rdm_migrator.transform import IdentityTransform, JSONTransformMixin

from ...transform.records import ZenodoRecordTransform


class DraftCreateAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM draft creation action."""

    name = "create-zenodo-draft"
    load_cls = load.DraftCreateAction

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
                    draft_pid = IdentityTransform()._transform(operation["after"])
            elif table_name == "files_bucket":
                bucket = IdentityTransform()._transform(operation["after"])
            elif table_name == "records_metadata":
                # need to json load the draft json
                # the parent json is calculated on transform
                self._load_json_fields(data=operation["after"], fields=["json"])
                draft_and_parent = ZenodoRecordTransform()._transform(
                    operation["after"]
                )

                draft = draft_and_parent["draft"]
                self._microseconds_to_isodate(
                    # expires_at will be ignored since the transformer returns a datetime
                    data=draft,
                    fields=["created", "updated", "expires_at"],
                )

                parent = draft_and_parent["parent"]
                self._microseconds_to_isodate(
                    data=parent,
                    fields=["created", "updated"],
                )

        # calculate pids
        parent["json"]["pid"] = generate_recid(data=None, status="K")
        draft["json"]["pid"] = {
            "pk": draft_pid["id"],
            "obj_type": "rec",
            "pid_type": "recid",
            "status": "K",
        }

        parent_pid = {
            "id": parent["json"]["pid"]["pk"],
            "pid_type": "recid",
            "pid_value": parent["json"]["id"],
            "status": "K",
            "object_type": "rec",
            # object_uuid is assigned by the pks generation of the load action
        }
        # assign json.pid to both parent and draft
        return dict(
            tx_id=self.tx.id,
            draft_pid=draft_pid,
            draft_bucket=bucket,
            draft=draft,
            parent_pid=parent_pid,
            parent=parent,
        )
