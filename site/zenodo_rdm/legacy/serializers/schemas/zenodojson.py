# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo serializer schemas."""

from marshmallow import Schema, fields, missing, post_dump
from marshmallow_utils.fields import SanitizedUnicode

from . import common


class ResourceTypeSchema(Schema):
    """Resource type schema."""

    type = fields.Str()
    subtype = fields.Str()
    title = fields.Str(attribute="title.en")

    @post_dump(pass_original=True)
    def dump_resource_type(self, result, original, **kwargs):
        """Dump resource type."""
        resource_type_id = original.get("id")
        if resource_type_id:
            _type = resource_type_id.split("-")[0]
            result["type"] = _type
            if "-" in resource_type_id:
                result["subtype"] = resource_type_id.split("-")[-1]
        return result


class JournalSchema(Schema):
    """Schema for a journal."""

    issue = fields.Str()
    pages = fields.Str()
    title = fields.Str()
    volume = fields.Str()
    year = fields.Str()


class MeetingSchema(Schema):
    """Schema for a meeting."""

    title = fields.Str()
    acronym = fields.Str()
    dates = fields.Str()
    place = fields.Str()
    url = fields.Str()
    session = fields.Str()
    session_part = fields.Str()


class ImprintSchema(Schema):
    """Schema for imprint."""

    publisher = fields.Str()
    place = fields.Str()
    isbn = fields.Str()


class PartOfSchema(Schema):
    """Schema for imprint."""

    pages = fields.Str()
    title = fields.Str()


class ThesisSchema(Schema):
    """Schema for thesis."""

    university = fields.Str()
    supervisors = fields.Nested(common.CreatorSchema, many=True)


class MetadataSchema(common.MetadataSchema):
    """Metadata schema for a record."""

    resource_type = fields.Nested(ResourceTypeSchema)

    journal = fields.Nested(JournalSchema, attribute="custom_fields.journal:journal")
    meeting = fields.Nested(MeetingSchema, attribute="custom_fields.meeting:meeting")
    imprint = fields.Nested(ImprintSchema, attribute="custom_fields.imprint:imprint")
    part_of = fields.Nested(PartOfSchema, attribute="custom_fields.part_of:part_of")
    thesis = fields.Nested(ThesisSchema, attribute="custom_fields.thesis:thesis")

    alternate_identifiers = fields.Method("dump_alternate_identifiers")

    license = fields.Nested({"id": fields.Function(lambda x: x)})
    grants = fields.Method("dump_grants")
    communities = fields.Method("dump_communities")
    relations = fields.Method("dump_relations")

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
            ret.append(legacy_grant)
        return ret or missing

    def dump_communities(self, obj):
        """Dump communities."""
        community_slugs = obj.get("_communities", [])
        if community_slugs:
            return [{"id": c} for c in community_slugs]
        return missing

    def dump_alternate_identifiers(self, obj):
        """Dump alternate identifiers."""
        result = []
        rel_id_schema = common.RelatedIdentifierSchema(exclude=("relation",))
        alternate_identifiers = obj.get("identifiers", [])
        for identifier in alternate_identifiers:
            result.append(
                rel_id_schema.dump(
                    {
                        "relation_type": {"id": "isAlternateIdentifier"},
                        "identifier": identifier["identifier"],
                    }
                )
            )
        return result or missing

    def dump_relations(self, obj):
        """Dump the relations to a dictionary."""
        # TODO: Figure out
        return {
            "version": [
                {
                    "index": obj["versions"]["index"] - 1,
                    "is_last": obj["versions"]["is_latest"],
                    # Cannot be generated because there is no relevant information in RDM
                    # "count": 1,
                    # "last_child": {"pid_type": "recid", "pid_value": "1235426"},
                    "parent": {"pid_type": "recid", "pid_value": obj["parent"]["id"]},
                }
            ]
        }


class StatsSchema(Schema):
    """Schema for usage statistics."""

    downloads = fields.Integer(attribute="all_versions.downloads")
    unique_downloads = fields.Integer(attribute="all_versions.unique_downloads")
    views = fields.Integer(attribute="all_versions.views")
    unique_views = fields.Integer(attribute="all_versions.unique_views")
    volume = fields.Integer(attribute="all_versions.volume")

    version_downloads = fields.Integer(attribute="this_version.downloads")
    version_unique_downloads = fields.Integer(attribute="this_version.unique_downloads")
    version_unique_views = fields.Integer(attribute="this_version.unique_views")
    version_views = fields.Integer(attribute="this_version.views")
    version_volume = fields.Integer(attribute="this_version.volume")


class ZenodoSchema(common.LegacySchema):
    """Schema for Zenodo records v1."""

    created = SanitizedUnicode()
    updated = SanitizedUnicode()
    recid = SanitizedUnicode(attribute="id", dump_only=True)
    revision = fields.Integer(attribute="revision_id")

    files = fields.Method("dump_files", dump_only=True)
    metadata = fields.Nested(MetadataSchema)

    owners = fields.Method("dump_owners")

    def dump_owners(self, obj):
        """Dump owners."""
        return [{"id": obj["parent"]["access"]["owned_by"]["user"]}]

    updated = fields.Str(dump_only=True)

    status = fields.Method("dump_status")

    def dump_status(self, obj):
        """Dump status."""
        if obj["is_draft"]:
            return "draft"
        return "published"

    stats = fields.Nested(StatsSchema)

    def dump_files(self, obj):
        """Dump files."""
        result = []
        files_url = obj["links"].get("files")
        for key, f in obj["files"].get("entries", {}).items():
            if files_url:
                links = {"self": f"{files_url}/{key}"}
                links["download"] = f"{links['self']}/content"
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
