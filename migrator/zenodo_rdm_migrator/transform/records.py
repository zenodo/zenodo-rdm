# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

from invenio_rdm_migrator.streams.records import RDMRecordTransform

from zenodo_rdm_migrator.errors import InvalidTombstoneRecord

from .entries.parents import ZENODO_DATACITE_PREFIX, ParentRecordEntry
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
            }

        return {
            "record": self._record(entry),
            "parent": self._parent(entry),
        }


class ZenodoDeletedRecordTransform(RDMRecordTransform):
    """Zenodo to RDM Record class for data transformation."""

    REMOVAL_REASONS_MAPPING = {
        "spam": "spam",
        "takedown": "take-down-request",
        "duplicate": "duplicate",
        "fraud": "fraud",
        "copyright": "copyright",
        "personal data": "personal-data",
        "misconduct": "misconduct",
        "test": "test-record",
    }

    def _parent(self, entry):
        """Extract a parent record."""
        transformed = {
            "created": entry.get("created"),
            "updated": entry.get("updated"),
            "version_id": entry.get("version_id"),
        }
        parent_pid = entry["json"].get("conceptrecid")
        transformed["json"] = {"id": parent_pid, "communities": {}}
        owner = next(iter(entry["json"].get("owners", [])), None)
        if owner is not None:
            transformed["json"]["access"] = {"owned_by": {"user": owner}}

        pids = {}
        doi = entry["json"].get("doi")
        conceptdoi = entry["json"].get("conceptdoi")
        if doi and doi.startswith(ZENODO_DATACITE_PREFIX):
            if conceptdoi:
                pids["doi"] = {
                    "client": "datacite",
                    "provider": "datacite",
                    "identifier": conceptdoi,
                }
            else:  # old Zenodo DOI record without concept DOI
                pids["doi"] = {"provider": "legacy", "identifier": ""}
        transformed["json"]["pids"] = pids

        return transformed

    def _draft(self, entry):
        """Transform the draft."""
        pass

    def _tombstone(self, entry):
        """Transform tombstone."""
        removal_json = entry.get("removal_json")
        if removal_json:
            removed_by = removal_json.get("removed_by") or None
            if isinstance(removed_by, int):
                removed_by = {"user": str(removed_by)}
            removal_date = entry.get("removal_date")

            removal_reason = None
            note = removal_json.get("removal_reason") or ""
            if note:
                if isinstance(note, list):
                    if len(note) == 2:
                        removal_reason, note = note
                        # NOTE: We sometimes used this format for takedowns only
                        if removal_reason == "takedown":
                            removal_reason = "take-down-request"
                    else:
                        removal_reason = None
                        note = ""
                elif isinstance(note, str):
                    note_words = note.lower().split()
                    for reason_match, reason_id in self.REMOVAL_REASONS_MAPPING.items():
                        if reason_match in note_words:
                            removal_reason = {"id": reason_id}
                            break

            return {
                "note": note,
                "is_visible": True,
                "removed_by": removed_by,
                "removal_date": removal_date,
                "citation_text": None,
                "removal_reason": removal_reason,
            }

    def _record(self, entry):
        """Extract a record."""
        tombstone = self._tombstone(entry)
        try:
            # We try our best the usual transformation
            res = ZenodoRecordEntry().transform(entry)
            res["json"]["tombstone"] = tombstone
            return res
        except Exception:
            # If that fails too, then we only need enough for a PID and tombstone
            recid = entry.get("recid", str(entry["json"].get("recid", "")))
            if not recid:
                raise InvalidTombstoneRecord()
            return {
                "created": entry.get("created"),
                "updated": entry.get("updated"),
                "version_id": entry.get("version_id"),
                "json": {"id": recid, "tombstone": tombstone},
                "index": entry.get("index", 0) + 1,
            }

    def _transform(self, entry):
        """Transform a single entry."""
        record = self._record(entry)
        if not record:
            raise InvalidTombstoneRecord()
        return {
            "record": record,
            "parent": self._parent(entry),
        }
