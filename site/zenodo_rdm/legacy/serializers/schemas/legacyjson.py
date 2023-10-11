# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy format serializer schemas."""

from marshmallow import fields, missing, post_dump, pre_dump
from marshmallow_utils.fields import SanitizedUnicode

from . import common


class MetadataSchema(common.MetadataSchema):
    """Metadata schema."""

    grants = fields.Method("dump_grants")

    def dump_grants(self, obj):
        """Dump grants from funding field."""
        funding = obj.get("funding", [])
        if not funding:
            return missing

        ret = []
        for funding_item in funding:
            award = funding_item.get("award")
            funder = funding_item.get("funder")
            legacy_grant = self._grant(award, funder)
            if not legacy_grant:
                continue
            grant_id = legacy_grant["internal_id"]
            if legacy_grant.get("program") == "FP7":
                grant_id = legacy_grant["code"]
            ret.append({"id": grant_id})
        return ret or missing

    license = SanitizedUnicode()

    journal_title = SanitizedUnicode(attribute="custom_fields.journal:journal.title")
    journal_volume = SanitizedUnicode(attribute="custom_fields.journal:journal.volume")
    journal_issue = SanitizedUnicode(attribute="custom_fields.journal:journal.issue")
    journal_pages = SanitizedUnicode(attribute="custom_fields.journal:journal.pages")

    conference_title = SanitizedUnicode(attribute="custom_fields.meeting:meeting.title")
    conference_acronym = SanitizedUnicode(
        attribute="custom_fields.meeting:meeting.acronym"
    )
    conference_dates = SanitizedUnicode(attribute="custom_fields.meeting:meeting.dates")
    conference_place = SanitizedUnicode(attribute="custom_fields.meeting:meeting.place")
    conference_url = SanitizedUnicode(attribute="custom_fields.meeting:meeting.url")
    conference_session = SanitizedUnicode(
        attribute="custom_fields.meeting:meeting.session"
    )
    conference_session_part = SanitizedUnicode(
        attribute="custom_fields.meeting:meeting.session_part"
    )

    # Imprint publisher does not exist in RDM, it comes from the record itself.
    imprint_publisher = SanitizedUnicode(attribute="publisher")
    imprint_isbn = SanitizedUnicode(attribute="custom_fields.imprint:imprint.isbn")
    imprint_place = SanitizedUnicode(attribute="custom_fields.imprint:imprint.place")

    partof_pages = SanitizedUnicode(attribute="custom_fields.imprint:imprint.pages")
    partof_title = SanitizedUnicode(attribute="custom_fields.imprint:imprint.title")

    thesis_university = SanitizedUnicode(attribute="custom_fields.thesis:university")

    embargo_date = fields.String(attribute="access.embargo.until")

    communities = fields.Method("dump_communities")

    def dump_communities(self, obj):
        """Dump communities."""
        community_slugs = obj.get("_communities", [])
        if community_slugs:
            return [{"identifier": c} for c in community_slugs]
        return missing

    @pre_dump
    def hook_alternate_identifiers(self, data, **kwargs):
        """Hooks 'identifiers' into related identifiers."""
        alternate_identifiers = data.get("identifiers", [])
        related_identifiers = data.get("related_identifiers", [])
        for identifier in alternate_identifiers:
            related_identifier = {
                "relation_type": {"id": "isalternateidentifier"},
                "identifier": identifier["identifier"],
                "scheme": identifier["scheme"],
            }
            related_identifiers.append(related_identifier)
        if related_identifiers:
            data["related_identifiers"] = related_identifiers
        return data

    @post_dump(pass_original=True)
    def dump_resource_type(self, result, original, **kwargs):
        """Dump resource type."""
        resource_type_id = original.get("resource_type", {}).get("id")
        if resource_type_id:
            upload_type = resource_type_id.split("-")[0]
            result["upload_type"] = upload_type
            if "-" in resource_type_id:
                result[f"{upload_type}_type"] = resource_type_id.split("-")[-1]
        return result


class LegacySchema(common.LegacySchema):
    """Legacy schema."""

    created = SanitizedUnicode()
    modified = SanitizedUnicode(attribute="updated")

    record_id = fields.Integer(attribute="id", dump_only=True)

    doi_url = SanitizedUnicode(attribute="links.doi", dump_only=True)

    metadata = fields.Nested(MetadataSchema, dump_only=True)
    title = SanitizedUnicode(
        attribute="metadata.title", dump_only=True, dump_default=""
    )

    owner = fields.Method("dump_owner", dump_only=True)

    files = fields.Method("dump_files", dump_only=True)

    state = fields.Method("dump_state", dump_only=True)
    submitted = fields.Bool(attribute="is_published")

    def dump_owner(self, obj):
        """Dump owner."""
        return obj["parent"]["access"]["owned_by"]["user"]

    def dump_files(self, obj):
        """Dump files."""
        result = []
        bucket_url = obj["links"].get("bucket")
        files_url = obj["links"].get("files")
        for key, f in obj["files"].get("entries", {}).items():
            file_id = f["id"]
            if files_url:
                links = {"self": f"{files_url}/{file_id}"}
            if bucket_url:
                links["download"] = f"{bucket_url}/{key}"
            result.append(
                {
                    "id": f["id"],
                    "filename": f["key"],
                    "filesize": f["size"],
                    # skip the checksum algorithm prefix
                    "checksum": f["checksum"].split(":", 1)[1],
                    "links": links,
                }
            )
        return result

    @pre_dump
    def hook_metadata(self, data, **kwargs):
        """Hooks up top-level fields under metadata."""
        data.setdefault("metadata", {})
        data["metadata"]["custom_fields"] = data.get("custom_fields")
        data["metadata"]["access"] = data["access"]
        data["metadata"]["pids"] = data.get("pids")
        data["metadata"]["parent"] = data.get("parent")
        return data

    def dump_state(self, obj):
        """Dump draft state."""
        state = "unsubmitted"
        if obj["is_published"]:
            state = "done"
            if obj["is_draft"]:
                state = "inprogress"
        return state

    @post_dump(pass_original=True)
    def dump_prereserve_doi(self, result, original, **kwargs):
        """Dump prereserved DOI information."""
        recid = original["id"]
        result["metadata"]["prereserve_doi"] = {
            "doi": f"10.5281/zenodo.{recid}",
            "recid": int(recid),
        }
        return result
