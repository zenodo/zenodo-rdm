# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

from invenio_rdm_migrator.streams.records import RDMRecordTransform

from .entries.records.record_files import ZenodoRDMRecordFileEntry
from .entries.records.records import ZenodoRecordEntry


class ZenodoRecordTransform(RDMRecordTransform):
    """Zenodo to RDM Record class for data transformation."""

    def _communities(self, entry):
        communities = entry["json"].get("communities")
        if communities:
            slugs = [slug for slug in communities]
            return {"ids": slugs, "default": slugs[0]}
        return {}

    def _parent(self, entry):
        parent = {
            "created": entry["created"],  # same as the record
            "updated": entry["updated"],  # same as the record
            "version_id": entry["version_id"],
            "json": {
                # loader is responsible for creating/updating if the PID exists.
                "id": entry["json"]["conceptrecid"],
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
        return None

    def _draft_files(self, entry):
        return None

    def _record_files(self, entry):
        def _update_files_with_record_information(file):
            return {
                **file,
                "created": entry["created"],  # we use the record's created date
                "updated": entry["updated"],  # we use the record's updated date
            }

        files = entry["json"]["_files"]
        if files:
            # add to files record information that will be used for populating the record files table
            _files_with_record_metadata = list(
                map(_update_files_with_record_information, files)
            )
            return list(
                map(ZenodoRDMRecordFileEntry().transform, _files_with_record_metadata)
            )
        else:
            return []
