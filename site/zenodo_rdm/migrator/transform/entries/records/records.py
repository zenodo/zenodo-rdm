# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

from datetime import datetime, timedelta

from invenio_rdm_migrator.streams.records import RDMRecordEntry

from .custom_fields import ZenodoCustomFieldsEntry
from .metadata import ZenodoDraftMetadataEntry, ZenodoRecordMetadataEntry

ZENODO_DATACITE_PREFIX = "10.5281"


class ZenodoRecordEntry(RDMRecordEntry):
    """Transform Zenodo record to RDM record."""

    def _id(self, entry):
        """Returns the rdm record uuid."""
        return entry["id"]

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
            _doi = record["doi"]
            if _doi.startswith(ZENODO_DATACITE_PREFIX):
                r["doi"] = {
                    "client": "datacite",
                    "provider": "datacite",
                    "identifier": record["doi"],
                }
            else:
                # external doi
                r["doi"] = {
                    "provider": "external",
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
        return ZenodoRecordMetadataEntry.transform(entry["json"])

    def _custom_fields(self, entry):
        """Transform custom fields."""
        return ZenodoCustomFieldsEntry.transform(entry["json"])


class ZenodoDraftEntry(ZenodoRecordEntry):
    """Zenodo draft transform.

    Many functions are identical to ZenodoRecordEntry but making the fields optional.
    """

    def _expires_at(self, entry):
        """Transform the expiry date of the draft."""
        next_year = datetime.today() + timedelta(days=365)

        # one year from the migration day
        return next_year.isoformat()

    def _fork_version_id(self, entry):
        """Transform the forked version of the draft."""
        # It is always None. It is calculated in the table generator
        # extracting it from the record version if it is in the cache.
        return None

    def _index(self, entry):
        """Returns the index of the record."""
        idx = entry.get("index")  # there are cases of {index: None}
        return idx + 1 if idx else 1  # in legacy we start at 0

    def _recid(self, entry):
        """Returns the recid of the draft."""
        legacy_recid = entry.get("_deposit", {}).get("pid", {}).get("value")
        return legacy_recid or entry["json"]["recid"]

    def _pids(self, entry):
        draft = entry["json"]
        r = {}

        # we only keep external "doi" for drafts as otherwise the
        # published record is used to enforce all pids to the draft
        # and "new" drafts don't have managed doi
        if draft.get("doi"):
            _doi = draft["doi"]
            if not _doi.startswith(ZENODO_DATACITE_PREFIX):
                # external doi
                r["doi"] = {
                    "provider": "external",
                    "identifier": draft["doi"],
                }

        return r

    def _access(self, entry):
        draft = entry["json"]
        access = draft.get("access_right")
        if not access:
            return {
                "record": "public",
                "files": "restricted",  # most restricted by default
            }
        else:
            return super()._access(entry)

    def _metadata(self, entry):
        """Transform the metadata of a record."""
        return ZenodoDraftMetadataEntry.transform(entry["json"])

    def transform(self, entry):
        """Transform a record single entry."""
        transformed = super().transform(entry)
        transformed["expires_at"] = self._expires_at(entry)
        transformed["fork_version_id"] = self._fork_version_id(entry)

        return transformed
