# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy deserializer schemas."""

from invenio_records.dictutils import clear_none
from marshmallow import RAISE, Schema, ValidationError, fields, post_load

from .metadata import MetadataSchema


class LegacySchema(Schema):
    """Transform a Zenodo legacy record to an RDM record."""

    class Meta:
        """Meta class."""

        unknown = RAISE

    metadata = fields.Nested(MetadataSchema)
    files = fields.Constant({"enabled": True})

    # Fields are added on post load:
    # custom_fields
    # access
    # pids

    @post_load(pass_original=True)
    def load_custom_fields(self, result, original, **kwargs):
        """Transform metadata into custom fields."""

        def _journal(data):
            """Load journal field."""
            if not data:
                return None

            journal_title = data.get("journal_title")
            journal_volume = data.get("journal_volume")
            journal_issue = data.get("journal_issue")
            journal_pages = data.get("journal_pages")

            rdm_journal = {
                "title": journal_title,
                "volume": journal_volume,
                "issue": journal_issue,
                "pages": journal_pages,
            }

            clear_none(rdm_journal)
            return rdm_journal

        def _meeting(data):
            """Load meeting field."""
            if not data:
                return None

            title = data.get("conference_title")
            acronym = data.get("conference_acronym")
            dates = data.get("conference_dates")
            place = data.get("conference_place")
            url = data.get("conference_url")
            session = data.get("conference_session")
            session_part = data.get("conference_session_part")

            rdm_meeting = {
                "title": title,
                "acronym": acronym,
                "dates": dates,
                "place": place,
                "url": url,
                "session": session,
                "session_part": session_part,
            }

            clear_none(rdm_meeting)
            return rdm_meeting

        def _imprint(data):
            """Load imprint field."""
            if not data:
                return None

            title = data.get("partof_title")
            pages = data.get("partof_pages")
            isbn = data.get("imprint_isbn")
            place = data.get("imprint_place")

            rdm_imprint = {
                "title": title,
                "pages": pages,
                "isbn": isbn,
                "place": place,
            }

            clear_none(rdm_imprint)
            return rdm_imprint

        metadata = original.get("metadata", {})
        journal = _journal(metadata)
        meeting = _meeting(metadata)
        imprint = _imprint(metadata)
        university = metadata.get("thesis_university")

        custom_fields = {
            "journal:journal": journal,
            "meeting:meeting": meeting,
            "imprint:imprint": imprint,
            "thesis:university": university,
        }

        clear_none(custom_fields)

        if custom_fields:
            result.setdefault("custom_fields", {})
            result["custom_fields"].update(custom_fields)

        return result

    @post_load(pass_original=True)
    def load_access(self, result, original, **kwargs):
        """Transform the access of a record."""

        def _embargoed_record(embargo_date):
            """Generates RDM access conditions based on legacy embargo conditions."""
            return {
                "record": "public",
                "files": "restricted",
                "embargo": {
                    "active": True,  # boolean
                    "until": embargo_date,  # ISO String
                },
            }

        def _restricted_record():
            """Generates RDM access conditions based on legacy restricted conditions."""
            return {
                "record": "public",
                "files": "restricted",
            }

        def _open_record():
            """Generates RDM access conditions for an open record."""
            return {
                "record": "public",
                "files": "public",
            }

        access = None
        metadata = original.get("metadata", {})
        access_right = metadata.get("access_right")
        embargo_date = metadata.get("embargo_date")

        is_embargoed = access_right == "embargoed"
        is_restricted = access_right == "restricted"
        is_open = access_right == "open"
        is_closed = access_right == "closed"

        if is_open or not access_right:
            access = _open_record()
        elif is_restricted or is_closed:
            # TODO access conditions are not yet implemented
            access = _restricted_record()
        elif is_embargoed and embargo_date:
            access = _embargoed_record(embargo_date)
        else:
            raise ValidationError("Unknown access type.")

        result["access"] = access
        return result

    @post_load(pass_original=True)
    def _pids(self, result, original, **kwargs):
        """Transform legacy doi in RDM pid with external provider."""
        metadata = original.get("metadata")
        if metadata:
            doi = metadata.get("doi")
            if doi:
                provider = "external"
                # TODO: Fetch prefix from config (or pass via schema context)
                if doi.startswith("10.5281/"):
                    provider = "datacite"
                result["pids"] = {"doi": {"identifier": doi, "provider": provider}}
        return result

    @post_load(pass_original=True)
    def load_communities(self, result, original, **kwargs):
        """Store the legacy communities field as a custom field."""
        communities = original.get("metadata", {}).get("communities", [])

        if communities:
            community_ids = [c["identifier"] for c in communities]
            result.setdefault("custom_fields", {})
            result["custom_fields"].update({"legacy:communities": community_ids})
        return result
