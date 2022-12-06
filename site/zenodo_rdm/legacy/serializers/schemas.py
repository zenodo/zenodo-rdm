# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy serializer schemas."""

from marshmallow import Schema, fields, post_dump
from marshmallow_utils.fields import SanitizedHTML, SanitizedUnicode


class FileSchema(Schema):
    """File schema."""

    key = SanitizedUnicode()
    size = fields.Number()
    checksum = SanitizedUnicode()


class CreatorSchema(Schema):
    """Creator schema."""

    name = SanitizedUnicode(attribute="person_or_org.name")
    affiliation = fields.Method("dump_affiliation")

    def dump_affiliation(self, obj):
        """Dump affiliation."""
        if obj.get("affiliations"):
            return obj["affiliations"][0]["name"]

    @post_dump(pass_original=True)
    def dump_identifiers(self, result, original, **kwargs):
        """Dump identifiers."""
        ids = original.get("person_or_org", {}).get("identifiers", [])
        if ids:
            for i in ids:
                if i["scheme"] == "orcid":
                    result["orcid"] = i["identifier"]
                if i["scheme"] == "gnd":
                    result["gnd"] = i["identifier"]
        return result


class MetadataSchema(Schema):
    """Metadata schema."""

    title = SanitizedUnicode()
    publication_date = SanitizedUnicode()
    description = SanitizedHTML()

    creators = fields.List(fields.Nested(CreatorSchema), dump_only=True)

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


class LegacySchema(Schema):
    """Legacy schema."""

    created = SanitizedUnicode()
    modified = SanitizedUnicode(attribute="updated")

    id = SanitizedUnicode(dump_only=True)
    record_id = SanitizedUnicode(attribute="id", dump_only=True)
    conceptrecid = SanitizedUnicode(attribute="parent.id", dump_only=True)

    metadata = fields.Nested(MetadataSchema, dump_only=True)
    title = SanitizedUnicode(
        attribute="metadata.title", dump_only=True, dump_default=""
    )

    links = fields.Raw(dump_only=True)

    owner = fields.Method("dump_owner", dump_only=True)

    def dump_owner(self, obj):
        """Dump owner."""
        return obj["parent"]["access"]["owned_by"][0]["user"]

    files = fields.Method("dump_files", dump_only=True)

    def dump_files(self, obj):
        """Dump files."""
        # TODO: pass files via service
        return []

    @post_dump(pass_original=True)
    def dump_state(self, result, original, **kwargs):
        """Dump draft state."""
        # TODO: Look into how to generate
        result["state"] = "unsubmitted"
        if original["is_published"]:
            result["state"] = "done"
            if original["is_draft"]:
                result["state"] = "inprogress"

        result["submitted"] = original["is_published"]
        return result

    @post_dump(pass_original=True)
    def dump_prereserve_doi(self, result, original, **kwargs):
        """Dump prereserved DOI information."""
        result["metadata"]["prereserve_doi"] = {
            "doi": original["pids"]["doi"]["identifier"],
            "recid": original["id"],
        }
        return result
