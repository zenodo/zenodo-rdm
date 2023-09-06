# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo RDM API classes."""

from invenio_drafts_resources.records.systemfields import ParentField
from invenio_pidstore.models import PIDStatus, RecordIdentifier
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_rdm_records.records.api import RDMDraft, RDMParent, RDMRecord
from invenio_records_resources.records.systemfields import PIDField


class DraftRecordIdProvider(RecordIdProvider):
    """Draft numerical auto-incrementing record ID provider."""

    default_status_with_obj = PIDStatus.NEW

    @classmethod
    def create(cls, object_type=None, object_uuid=None, options=None, **kwargs):
        """Create a new record identifier."""
        assert "pid_value" not in kwargs

        kwargs["pid_value"] = str(RecordIdentifier.next())
        kwargs.setdefault("status", cls.default_status)

        if object_type and object_uuid:
            kwargs["status"] = cls.default_status_with_obj

        return super(RecordIdProvider, cls).create(
            object_type=object_type, object_uuid=object_uuid, **kwargs
        )


class ZenodoRDMParent(RDMParent):
    """Zenodo RDMParent API class."""

    pid = PIDField("id", provider=DraftRecordIdProvider, delete=True)


class ZenodoRDMRecord(RDMRecord):
    """Zenodo RDMRecord API class."""

    pid = PIDField("id", provider=DraftRecordIdProvider, delete=True)
    parent_record_cls = ZenodoRDMParent

    parent = ParentField(
        ZenodoRDMParent, create=False, soft_delete=False, hard_delete=False
    )


class ZenodoRDMDraft(RDMDraft):
    """Zenodo RDMDraft API class."""

    pid = PIDField("id", provider=DraftRecordIdProvider, delete=False)
    parent_record_cls = ZenodoRDMParent

    parent = ParentField(
        ZenodoRDMParent, create=True, soft_delete=False, hard_delete=True
    )
