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

ZENODO_DATACITE_PREFIX = "10.5281/"


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

    def __init__(self, partial=False):
        """Constructor.

        :param partial: a boolean enabling partial transformations, i.e. missing keys.
        """
        self.partial = partial

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
        # some legacy records have different pid value in deposit than record
        # however _deposit.pid.value would contain the correct one
        # if it is not legacy we get it from the current field (json.id)
        legacy_recid = entry["json"].get("_deposit", {}).get("pid", {}).get("value")
        return str(legacy_recid or entry["json"]["recid"])

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

    def _bucket_id(self, entry):
        """Transform the bucket of a draft."""
        return entry["json"]["_buckets"]["deposit"]

    def _media_bucket_id(self, entry):
        """Transform the media bucket of a draft."""
        return entry["json"]["_buckets"].get("extra_formats")

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
        keys = [
            "id",
            "created",
            "updated",
            "version_id",
            "index",
            "bucket_id",
            "media_bucket_id",
            "expires_at",
            "fork_version_id",
        ]

        transformed = {}
        for key in keys:
            func = getattr(self, "_" + key)
            try:
                transformed[key] = func(entry)
            # this might mask nested missing keys, it is still a partial transformation
            # full one (with more validation) should be checked on a record
            except KeyError as ex:
                if not self.partial:
                    raise KeyError(ex)
                pass

        # json might give an inner KeyError that should not be masked
        if "json" in entry:
            transformed["json"] = {
                "id": self._recid(entry),
                "pids": self._pids(entry),
                "files": self._files(entry),
                "media_files": self._media_files(entry),
                "metadata": self._metadata(entry),
                "access": self._access(entry),
                "custom_fields": self._custom_fields(entry),
            }
        elif not self.partial:
            raise KeyError("json")
        # else, pass

        return transformed
