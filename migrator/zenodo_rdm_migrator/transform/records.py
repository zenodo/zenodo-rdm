# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

from invenio_rdm_migrator.streams.records import RDMRecordTransform

from .entries.parents import ParentRecordEntry
from .entries.records.record_files import ZenodoRDMRecordFileEntry
from .entries.records.records import ZenodoDraftEntry, ZenodoRecordEntry


class ZenodoRecordTransform(RDMRecordTransform):
    """Zenodo to RDM Record class for data transformation."""

    def _parent(self, entry):
        """Extract a parent record."""
        return ParentRecordEntry().transform(entry)

    def _record(self, entry):
        """Extract a record."""
        return ZenodoRecordEntry().transform(entry)

    def _draft(self, entry):
        """Extract a draft."""
        return ZenodoDraftEntry().transform(entry)

    def _file_records(self, entry):
        """Transform file records for an entry."""
        files = entry["json"].get("_files", [])
        return list(map(ZenodoRDMRecordFileEntry(context=entry).transform, files))

    def _draft_files(self, entry):
        """Transform file records of a record."""
        # draft files are migrated as post load since new versions/new drafts
        # do not have _files until they are saved so we cannot rely on it
        return {}

    def _record_files(self, entry):
        """Transform file records of a record."""
        return self._file_records(entry)

    def _transform(self, entry):
        """Transform a single entry."""
        is_draft = "deposits" in entry["json"]["$schema"]

        if is_draft:
            draft = self._draft(entry)
            parent = self._parent(entry)

            # Draft communities are handled in a special way for legacy drafts
            community_slugs = parent["json"].get("communities", {}).get("ids")
            parent["json"]["communities"] = {}
            if community_slugs:
                draft["json"]["custom_fields"]["legacy:communities"] = community_slugs
            return {
                "draft": draft,
                "parent": parent,
                "draft_files": self._draft_files(entry),
            }

        return {
            "record": self._record(entry),
            "parent": self._parent(entry),
            "record_files": self._record_files(entry),
        }
