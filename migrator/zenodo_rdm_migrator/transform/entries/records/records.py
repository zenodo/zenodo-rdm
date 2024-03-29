# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

import random
from datetime import datetime, timedelta

from invenio_rdm_migrator.streams.records import RDMRecordEntry

from .custom_fields import ZenodoCustomFieldsEntry
from .metadata import ZenodoDraftMetadataEntry, ZenodoRecordMetadataEntry

ZENODO_DATACITE_PREFIXES = (
    "10.5281/",
    "10.5072/",  # Test DOI prefix, useful for tests
)


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
            if _doi.startswith(ZENODO_DATACITE_PREFIXES):
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

    def _bucket_id(self, entry):
        """Transform the bucket of a record."""
        return entry["json"]["_buckets"].get("record")

    def _media_bucket_id(self, entry):
        """Transform the media bucket of a record."""
        return entry["json"]["_buckets"].get("extra_formats")

    def _files(self, entry):
        """Transform the files of a record."""
        return {"enabled": True}

    def _media_files(self, entry):
        """Transform the media files of a record."""
        return {"enabled": self._media_bucket_id(entry) is not None}

    def _access(self, entry):
        record = entry["json"]
        access_right = record.get("access_right")
        is_open = access_right in ("open", None)
        r = {
            "record": "public",
            "files": "public" if is_open else "restricted",
        }
        if access_right == "embargoed":
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
        next_year = (
            datetime.today()
            + timedelta(days=365)
            # We add a bit of "noise" so that not all drafts expire at the same time
            + timedelta(days=random.randrange(10, 100))
        )

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
        # some legacy records have different pid value in deposit than record
        # however _deposit.pid.value would contain the correct one
        # if it is not legacy we get it from the current field (json.id)
        legacy_recid = entry["json"].get("_deposit", {}).get("pid", {}).get("value")
        if not legacy_recid:
            # It's a new draft, so there's no "pid" key yet
            legacy_recid = entry["json"].get("_deposit", {}).get("id")
        return str(legacy_recid or entry["json"]["recid"])

    def _pids(self, entry):
        draft = entry["json"]
        r = {}

        # we only keep external "doi" for drafts as otherwise the
        # published record is used to enforce all pids to the draft
        # and "new" drafts don't have managed doi
        if draft.get("doi"):
            _doi = draft["doi"]
            if not _doi.startswith(ZENODO_DATACITE_PREFIXES):
                # external doi
                r["doi"] = {
                    "provider": "external",
                    "identifier": draft["doi"],
                }

        return r

    def _bucket_id(self, entry):
        """Transform the bucket of a draft."""
        return entry["json"]["_buckets"]["deposit"]

    def _media_bucket_id(self, entry):
        """Transform the media bucket of a draft."""
        return entry["json"]["_buckets"].get("extra_formats")

    def _metadata(self, entry):
        """Transform the metadata of a record."""
        return ZenodoDraftMetadataEntry.transform(entry["json"])

    def transform(self, entry):
        """Transform a record single entry."""
        transformed = {}
        self._load_partial(
            entry,
            transformed,
            [
                "id",
                "created",
                "updated",
                "version_id",
                "index",
                "bucket_id",
                "media_bucket_id",
                "expires_at",
                "fork_version_id",
            ],
        )
        # json might give an inner KeyError that should not be masked
        self._load_partial(
            entry,
            transformed,
            [
                ("id", "recid"),
                ("$schema", "schema"),
                "pids",
                "files",
                "media_files",
                "metadata",
                "access",
                "custom_fields",
            ],
            prefix="json",
        )

        return transformed
