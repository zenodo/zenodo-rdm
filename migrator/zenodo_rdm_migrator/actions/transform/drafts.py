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

from ...transform.entries.parents import ParentRecordEntry
from ...transform.entries.records.records import ZenodoDraftEntry


class DraftTransformMixin(JSONTransformMixin):
    """Draft transformation mixin class."""

    def _draft_and_parent_from_op(self, op_data):
        """Transform a draft and parent from an operation data.

        Assumes this mixin is used in a TransformAction.
        """
        # need to json load the draft json
        # the parent json is calculated on transform
        self._load_json_fields(data=op_data, fields=["json"])

        # draft
        draft = ZenodoDraftEntry(partial=True).transform(op_data)
        self._microseconds_to_isodate(
            # expires_at will be ignored since the transformer returns a datetime
            data=draft,
            fields=["created", "updated", "expires_at"],
        )
        # parent
        parent = ParentRecordEntry(partial=True).transform(op_data)
        # FIXME: draft communities could be review or addition
        # we might need to differentiate those
        if "json" in parent:
            parent["json"]["communities"] = {}
        self._microseconds_to_isodate(
            data=parent,
            fields=["created", "updated"],
        )

        return draft, parent


class DraftCreateAction(TransformAction, DraftTransformMixin):
    """Zenodo to RDM draft creation action."""

    name = "create-zenodo-draft"
    load_cls = load.DraftCreateAction

    @classmethod
    def matches_action(cls, tx):
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

    def _transform_data(self):
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
                draft, parent = self._draft_and_parent_from_op(operation["after"])

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


class DraftEditAction(TransformAction, DraftTransformMixin):
    """Zenodo to RDM draft creation action."""

    name = "edit-zenodo-draft"
    load_cls = load.DraftEditAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]
        table_name = op["source"]["table"]
        op_type = op["op"]

        # no need to differentiate from record update since we wont do that in support
        # and user edits (e.g. web ui) pass by a draft (create + [edit] + publish actions)
        return table_name == "records_metadata" and op_type == OperationType.UPDATE

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        operation = self.tx.operations[0]
        draft, parent = self._draft_and_parent_from_op(operation["after"])
        return dict(tx_id=self.tx.id, draft=draft, parent=parent)


class DraftPublishAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM draft publishing action."""

    name = "publish-zenodo-draft"
    load_cls = load.DraftPublishAction

    @classmethod
    def matches_action(cls, tx):  # pragma: no cover
        """Checks if the data corresponds with that required by the action."""
        insert_pid_redirect = False
        delete_pid_relation = False

        recid_ops = {}
        for operation in tx.operations:
            table_name = operation["source"]["table"]
            if (
                table_name == "pidstore_pid"
                and operation["after"]["pid_type"] == "recid"
            ):
                is_update = operation["op"] == OperationType.UPDATE
                if not is_update:
                    return False

                pid_id = operation["after"]["id"]
                cur_cnt = recid_ops.get(pid_id, {}).get("count", 0)
                recid_ops[pid_id] = {
                    "count": cur_cnt + 1,
                    "status": operation["after"]["status"],
                }
            elif table_name == "pidstore_redirect":
                insert_pid_redirect = operation["op"] == OperationType.INSERT
            elif table_name == "pidrelations_pidrelation":
                delete_pid_relation = operation["op"] == OperationType.DELETE

        if not insert_pid_redirect or not delete_pid_relation:
            return False

        # recid
        # draft 3 UPDATES, final state R
        # parent 2 UPDATES, final state M
        if len(recid_ops) != 2:
            return False
        # order of lsn is respected therefore they come in order
        # and the first operations are done on the draft pid
        recid_ops = list(recid_ops.values())
        draft = recid_ops[0]
        parent = recid_ops[1]
        recid_rules = (
            draft["count"] == 3
            and draft["status"] == "R"
            and parent["count"] == 2
            and parent["status"] == "M"
        )
        # the next ones are optional (not checked)
        # doi
        # parent 1 INSERT, final state K
        # draft 1 INSERT, final state K
        # oai
        # draft 1 INSERT, final state R

        # at the moment we only check operations over pids
        # should be enough to differentiate between different types of publishing
        # the operations over files/buckets can vary depending on the number of files
        # the same happens with records and number of communities, etc.
        return recid_rules

    def _transform_data(self):  # pragma: no cover
        """Transforms the data and returns an instance of the mapped_cls."""
        return dict(
            tx_id=self.tx.id,
            # pids
            # versioning and pid related ops will be taken care by the load action
            parent_pid={},  # to update
            draft_pid={},  # to delete
            record_pid={},  # to register
            parent_doi={},  # to reserve
            record_doi={},  # to reserve
            record_oai={},  # to register
            # bucket
            # would it be smart to just reference the record? to avoid passing/recreating
            # all files objects? (similart to what we do in RDM?)
            draft_bucket={},  # to delete
            record_bucket={},  # to create
            # metadata would be made into a record by the load action
            parent={},
            draft={},
        )
