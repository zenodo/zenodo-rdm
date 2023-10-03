# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration drafts actions module."""


from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load
from invenio_rdm_migrator.transform import DatetimeMixin, JSONTransformMixin

from ...transform.records import ZENODO_DATACITE_PREFIXES, ZenodoRecordTransform


class DraftTransformMixin(JSONTransformMixin, DatetimeMixin):
    """Draft transformation mixin class."""

    def _parse_record(self, op_data):
        """Transform a draft and parent from an operation data.

        Assumes this mixin is used in a TransformAction.
        """
        # ops don't have JSON already parsed
        self._load_json_fields(data=op_data, fields=["json"])
        self._microseconds_to_isodate(data=op_data, fields=["created", "updated"])
        return ZenodoRecordTransform(partial=True)._transform(op_data)


class DraftCreateAction(TransformAction, DraftTransformMixin):
    """Zenodo to RDM draft creation action."""

    name = "create-zenodo-draft"
    load_cls = load.DraftCreateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        ops = tx.as_ops_tuples(
            include=(
                "records_metadata",
                "pidstore_pid",
                "files_bucket",
                "pidstore_recid",
                "records_buckets",
                "pidrelations_pidrelation",
            )
        )

        create_ops = [
            ("pidstore_recid", OperationType.INSERT),
            ("pidstore_pid", OperationType.INSERT),
            ("pidstore_recid", OperationType.INSERT),
            ("pidstore_pid", OperationType.INSERT),
            ("pidstore_pid", OperationType.INSERT),
            ("files_bucket", OperationType.INSERT),
            ("records_metadata", OperationType.INSERT),
            ("records_buckets", OperationType.INSERT),
            ("pidrelations_pidrelation", OperationType.INSERT),
            ("pidrelations_pidrelation", OperationType.UPDATE),
            ("pidrelations_pidrelation", OperationType.INSERT),
        ]
        return ops == create_ops

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        # draft files should be a separate transaction
        _, bucket = self.tx.ops_by("files_bucket").popitem()
        _, draft_row = self.tx.ops_by("records_metadata").popitem()
        res = self._parse_record(draft_row)
        draft = res.get("draft")
        parent = res.get("parent")
        assert draft and parent

        return dict(
            pid={
                "created": draft["created"],
                "updated": draft["updated"],
                "pid_value": draft["json"]["id"],
            },
            draft=draft,
            draft_bucket=bucket,
            parent_pid={
                "created": parent["created"],
                "updated": parent["updated"],
                "pid_value": parent["json"]["id"],
            },
            parent=parent,
        )


class DraftEditAction(TransformAction, DraftTransformMixin):
    """Zenodo to RDM draft creation action."""

    name = "edit-zenodo-draft"
    load_cls = load.DraftEditAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) not in (1, 2):
            return False

        ops = [(op["source"]["table"], op["op"]) for op in tx.operations]

        has_record_update = ops.count(("records_metadata", OperationType.UPDATE)) == 1
        has_bucket_update = ops.count(("files_bucket", OperationType.UPDATE)) == 1
        if len(ops) == 2:
            # External DOI edit action
            return has_record_update and has_bucket_update
        else:
            # Edit action or draft update
            return has_record_update

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        bucket = None
        buckets = self.tx.ops_by("files_bucket")
        if buckets:
            _, bucket = buckets.popitem()
        _, draft_row = self.tx.ops_by("records_metadata").popitem()
        res = self._parse_record(draft_row)
        draft = res.get("draft")
        parent = res.get("parent")
        assert draft and parent
        return dict(draft=draft, parent=parent, bucket=bucket)


"""
For publishing drafts there are 3 main cases:

A. Publish of first draft
    1. Zenodo DOI
        - PIDs
            - UPDATE pidstore_pid, recid, status = REGISTERED + object_uuid = record.id
            - UPDATE pidstore_pid, conceptrecid, status = REDIRECTED + object_uuid = redirect->recid
            - INSERT pidstore_pid, doi, status = RESERVED + object_uuid = record.id
            - INSERT pidstore_pid, conceptdoi, status = REDIRECT + object_uuid = redirect->conceptrecid
            - INSERT pidstore_pid, oai, status = REGISTERED + object_uuid = record.id
        - Records/drafts metadata
            - UPDATE records_metadata, draft, status -> published
            - INSERT records_metadata, record, copy from draft
        - Files
            - UPDATE files_bucket, draft_bucket, lock = True
            - INSERT files_bucket, record_bucket, "snapshot" from draft_bucket
            - INSERT records_buckets, record.id <-> record_bucket
            - N(files) x INSERT files_object, record_files, copied from draft_bucket to record_bucket
    2. External DOI
        - PIDs
            - UPDATE pidstore_pid, recid, status = REGISTERED + object_uuid = record.id
            - UPDATE pidstore_pid, conceptrecid, status = REDIRECTED + object_uuid = redirect->recid
            - INSERT pidstore_pid, doi, status = RESERVED + object_uuid = record.id
            - INSERT pidstore_pid, oai, status = REGISTERED + object_uuid = record.id
        - Records/drafts metadata
            - UPDATE records_metadata, draft, status -> published
            - INSERT records_metadata, record, copy from draft
        - Files
            - UPDATE files_bucket, draft_bucket, lock = True
            - INSERT files_bucket, record_bucket, "snapshot" from draft_bucket
            - INSERT records_buckets, record.id <-> record_bucket
            - N(files) x INSERT files_object, record_files, copied from draft_bucket to record_bucket

B. Publish of edit
    1. Zenodo DOI
        - Records/drafts metadata
            - UPDATE records_metadata, draft, status -> published
            - UPDATE records_metadata, record, copy from draft
    2. External DOI
        a. w/o files modifications
            - Records/drafts metadata
                - UPDATE records_metadata, draft, status -> published
                - UPDATE records_metadata, record, copy from draft
            - Files
                - UPDATE files_bucket, record_bucket, lock = False
                - UPDATE files_bucket, record_bucket, lock = True
                - UPDATE files_bucket, draft_bucket, lock = True
        b. w/ files modifications
            - Records/drafts metadata
                - UPDATE records_metadata, draft, status -> published
                - UPDATE records_metadata, record, copy from draft
            - Files
                - UPDATE files_bucket, draft_bucket, lock = True
                - INSERT files_bucket, record_bucket, "snapshot" from draft_bucket
                - INSERT records_buckets, record.id <-> record_bucket
                - N(files) x INSERT files_object, record_files, copied from draft_bucket to record_bucket
        c{a,b}. change of external DOI
            - PIDs
                - UPDATE pidstore_pid, recid, status = REGISTERED + object_uuid = record.id
                - UPDATE pidstore_pid, conceptrecid, status = REDIRECTED + object_uuid = redirect->recid
                - DELETE pidstore_pid, old_doi
                - INSERT pidstore_pid, new_doi, status = RESERVED + object_uuid = record.id
            - Records/drafts metadata - same as {a,b}
            - Files - same as {a,b}

C. Publish of new version
    1. Zenodo DOI
        - PIDs
            - UPDATE pidstore_pid, recid, status = REGISTERED + object_uuid = record.id
            - UPDATE pidstore_pid, conceptrecid, status = REDIRECTED + object_uuid = redirect->latest_recid
            - INSERT pidstore_pid, doi, status = RESERVED + object_uuid = record.id
            - INSERT pidstore_pid, oai, status = REGISTERED + object_uuid = record.id
        - Records/drafts metadata
            - UPDATE records_metadata, draft, status -> published
            - INSERT records_metadata, record, copy from draft
        - Files
            - UPDATE files_bucket, draft_bucket, lock = True
            - INSERT files_bucket, record_bucket, "snapshot" from draft_bucket
            - INSERT records_buckets, record.id <-> record_bucket
            - N(files) x INSERT files_object, record_files, copied from draft_bucket to record_bucket
"""


class DraftPublishNewAction(TransformAction, DraftTransformMixin):
    """Zenodo to RDM publish of a new draft (first publish or new version) action."""

    name = "publish-new-draft"
    load_cls = load.DraftPublishNewAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        records = tx.ops_by("records_metadata", group_id="id")
        if not records:
            return False

        record = None
        for metadata in records.values():
            cls._load_json_fields(data=metadata, fields=["json"])
            is_record = "deposit" not in metadata.get("$schema", "")
            if is_record:
                record = metadata
                break

        if not record:
            return False

        parent_doi_value = record.get("conceptdoi")
        has_doi = record.get("doi") is not None
        is_local_doi = has_doi and parent_doi_value is not None
        parent_doi_ops = tx.filter_ops(
            "pidstore_pid",
            filter={"pid_type": "doi", "pid_value": parent_doi_value},
        )
        has_parent_doi_insert = any(
            o["op"] == OperationType.INSERT for o in parent_doi_ops
        )

        #
        # A{1,2}
        #
        if is_local_doi:
            is_first_draft_publish = has_parent_doi_insert
        else:
            oai_ops = tx.filter_ops("pidstore_pid", filter={"pid_type": "oai"})
            has_oai_insert = any(o["op"] == OperationType.INSERT for o in oai_ops)
            is_first_draft_publish = has_oai_insert
        #
        # C1
        #
        is_new_version_publish = is_local_doi and not has_parent_doi_insert

        return is_first_draft_publish or is_new_version_publish

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        pids = self.tx.ops_by("pidstore_pid", group_key=("pid_type", "pid_value"))
        buckets = self.tx.ops_by("files_bucket")
        records = self.tx.ops_by("records_metadata")
        object_versions = self.tx.ops_by(
            "files_object",
            group_id=("bucket_id", "key", "version_id"),
        )

        record, draft, parent = None, None, None
        for record_row in records.values():
            res = self._parse_record(record_row)
            if res.get("record"):
                record = res["record"]
                parent = res["parent"]
            if res.get("draft"):
                draft = res["draft"]
                if not record:
                    parent = res["parent"]
        assert record and draft and parent

        record_bucket, draft_bucket = None, None
        for bucket_id, bucket in buckets.items():
            if record.get("bucket_id") == bucket_id:
                record_bucket = bucket
            if draft.get("bucket_id") == bucket_id:
                draft_bucket = bucket
        assert record_bucket and draft_bucket

        assert all(
            ov["bucket_id"] == record_bucket["id"] for ov in object_versions.values()
        )
        record_object_versions = list(object_versions.values())

        pid = pids.get(("recid", record["json"]["id"]))
        doi = pids.get(("doi", record["json"]["pids"]["doi"]["identifier"]))
        oai_pid = pids.get(("oai", record["json"]["pids"]["oai"]["identifier"]))
        parent_pid = pids.get(("recid", parent["json"]["id"]))
        parent_doi_value = (
            parent["json"].get("pids", {}).get("doi", {}).get("identifier")
        )
        parent_doi = pids.get(("doi", parent_doi_value))
        return dict(
            # pids
            pid=pid,
            parent_pid=parent_pid,
            doi=doi,
            parent_doi=parent_doi,
            oai_pid=oai_pid,
            # records
            parent=parent,
            draft=draft,
            record=record,
            # bucket
            draft_bucket=draft_bucket,
            record_bucket=record_bucket,
            record_object_versions=record_object_versions,
        )


class DraftPublishEditAction(TransformAction, DraftTransformMixin):
    """Zenodo to RDM publish of an edited draft action."""

    name = "publish-edit-draft"
    load_cls = load.DraftPublishEditAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        # Quick checks to avoid conflicts
        records = tx.ops_by("records_metadata", group_id="id")
        if not records or len(records) != 2:
            return False

        record = None
        for metadata in records.values():
            cls._load_json_fields(data=metadata, fields=["json"])
            is_record = "deposit" not in metadata.get("$schema", "")
            if is_record:
                record = metadata
                break

        if not record:
            return False

        parent_doi_value = record.get("conceptdoi")
        has_doi = record.get("doi") is not None
        is_local_doi = has_doi and parent_doi_value is not None
        parent_doi_ops = tx.filter_ops(
            "pidstore_pid",
            filter={"pid_type": "doi", "pid_value": parent_doi_value},
        )
        has_parent_doi_insert = any(
            o["op"] == OperationType.INSERT for o in parent_doi_ops
        )

        #
        # A{1,2}
        #
        if is_local_doi:
            is_first_draft_publish = has_parent_doi_insert
        else:
            oai_ops = tx.filter_ops("pidstore_pid", filter={"pid_type": "oai"})
            has_oai_insert = any(o["op"] == OperationType.INSERT for o in oai_ops)
            is_first_draft_publish = has_oai_insert
        #
        # C1
        #
        is_new_version_publish = is_local_doi and not has_parent_doi_insert

        #
        # B{1,2}
        #
        is_publish_edit = not (is_first_draft_publish or is_new_version_publish)
        return is_publish_edit

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        pids = self.tx.ops_by("pidstore_pid", group_key=("pid_type", "pid_value"))
        buckets = self.tx.ops_by("files_bucket")
        records = self.tx.ops_by("records_metadata")
        object_versions = self.tx.ops_by(
            "files_object",
            group_id=("bucket_id", "key", "version_id"),
        )

        record, draft, parent = None, None, None
        for record_row in records.values():
            res = self._parse_record(record_row)
            if res.get("record"):
                record = res["record"]
                parent = res["parent"]
            if res.get("draft"):
                draft = res["draft"]
                if not record:
                    parent = res["parent"]
        assert record and draft and parent

        # Figure out in which scenario we are:
        record_bucket, draft_bucket = None, None
        record_object_versions = None
        old_external_doi, new_external_doi = None, None
        doi_value = record["json"]["pids"]["doi"]["identifier"]
        doi = pids.get(("doi", doi_value))
        is_local_doi = doi_value.startswith(ZENODO_DATACITE_PREFIXES)
        if not is_local_doi:
            # Check if it's an external DOI change
            doi_ops = self.tx.filter_ops("pidstore_pid", filter={"pid_type": "doi"})
            has_doi_delete = any(o["op"] == OperationType.DELETE for o in doi_ops)
            is_external_doi_change = not is_local_doi and has_doi_delete
            if is_external_doi_change:
                new_external_doi = doi
                old_external_doi = next(
                    iter(
                        v
                        for v in pids.values()
                        if v["pid_type"] == "doi" and v["pid_Value"] != doi_value
                    )
                )

            # Check if we also have file changes
            has_files_ops = (
                len(self.tx.as_ops_tuples(include=("files_object", "files_files"))) == 0
            )
            if has_files_ops:
                for bucket_id, bucket in buckets.items():
                    if record.get("bucket_id") == bucket_id:
                        record_bucket = bucket
                    if draft.get("bucket_id") == bucket_id:
                        draft_bucket = bucket
                assert record_bucket and draft_bucket
                assert all(
                    ov["bucket_id"] == record_bucket["id"]
                    for ov in object_versions.values()
                )
                record_object_versions = list(object_versions.values())

        return dict(
            # Records
            parent=parent,
            draft=draft,
            record=record,
            # Files
            draft_bucket=draft_bucket,
            record_bucket=record_bucket,
            record_object_versions=record_object_versions,
            # PIDs
            old_external_doi=old_external_doi,
            new_external_doi=new_external_doi,
        )


DRAFT_ACTIONS = [
    DraftCreateAction,
    DraftEditAction,
    DraftPublishNewAction,
    DraftPublishEditAction,
]
