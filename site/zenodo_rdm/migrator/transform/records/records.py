# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

from invenio_rdm_migrator.streams.records import RDMRecordEntry, RDMRecordTransform

from .custom_fields import ZenodoCustomFieldsEntry
from .metadata import ZenodoMetadataEntry


class ZenodoRecordEntry(RDMRecordEntry):
    """Transform Zenodo record to RDM record."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return entry["version_id"]

    def _index(self, entry):
        """Returns the index of the record."""
        return entry.get("index", 0) + 1  # in legacy we start at 0

    def _recid(self, entry):
        """Returns the recid of the record."""
        return str(entry["json"]["recid"])

    def _pids(self, entry):
        record = entry["json"]
        r = {
            "oai": {
                "provider": "oai",
                "identifier": record["_oai"]["id"],
            },
        }
        if record.get("doi"):
            r["doi"] = {
                "client": "datacite",
                "provider": "datacite",
                "identifier": record["doi"],
            }

        return r

    def _files(self, entry):
        """Transform the files of a record."""
        return {"enabled": True}

    def _access(self, entry):
        record = entry["json"]
        is_open = record["access_right"] == "open"
        r = {
            "record": "public",
            "files": "public" if is_open else "restricted",
        }
        if record["access_right"] == "embargoed":
            r["embargo"] = {
                "until": record["embargo_date"],
                "active": True,
            }
        return r

    def _metadata(self, entry):
        """Transform the metadata of a record."""
        return ZenodoMetadataEntry.transform(entry["json"])

    def _custom_fields(self, entry):
        """Transform custom fields."""
        return ZenodoCustomFieldsEntry.transform(entry["json"])


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
        files = entry["json"].get("_files", [])
        return [
            {
                "key": f["key"],
                "object_version": {
                    "file": {
                        "size": f["size"],
                        "checksum": f["checksum"],
                    },
                },
            }
            for f in files
        ]
