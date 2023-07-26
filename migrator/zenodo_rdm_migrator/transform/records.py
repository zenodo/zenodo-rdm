# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

import json

from invenio_rdm_migrator.streams.records import RDMRecordTransform

from ..errors import NoConceptRecidForDraft
from .entries.records.record_files import ZenodoRDMRecordFileEntry
from .entries.records.records import ZenodoDraftEntry, ZenodoRecordEntry


class ZenodoRecordTransform(RDMRecordTransform):
    """Zenodo to RDM Record class for data transformation."""

    def _communities(self, entry):
        communities = entry["json"].get("communities")
        if communities:
            slugs = [slug for slug in communities]
            return {"ids": slugs, "default": slugs[0]}
        return {}

    def _parent(self, entry):
        # check if conceptrecid exists and bail otherwise
        # this is the case for some deposits and they should be fixed in prod as it
        # should not happen!
        parent_pid = entry["json"].get("conceptrecid")
        if not parent_pid:
            # we raise so the error logger writes these cases in the log file
            raise NoConceptRecidForDraft(draft=entry)
        parent = {
            "created": entry["created"],  # same as the record
            "updated": entry["updated"],  # same as the record
            "version_id": entry["version_id"],
            "json": {
                # loader is responsible for creating/updating if the PID exists.
                "id": parent_pid,
                "access": {
                    "owned_by": [{"user": o} for o in entry["json"].get("owners", [])]
                },
                "communities": self._communities(entry),
            },
        }

        return parent

    def _record(self, entry):
        return ZenodoRecordEntry().transform(entry)

    def _draft(self, entry):
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
            # FIXME: draft communities could be review or addition
            # we might need to differentiate those
            parent = self._parent(entry)
            parent["json"]["communities"] = {}
            return {
                "draft": self._draft(entry),
                "parent": parent,
                "draft_files": self._draft_files(entry),
            }

        return {
            "record": self._record(entry),
            "parent": self._parent(entry),
            "record_files": self._record_files(entry),
        }
