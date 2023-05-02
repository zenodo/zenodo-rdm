# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy serializer schemas."""

from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError
from invenio_records_resources.proxies import current_service_registry
from marshmallow import Schema, fields, missing, post_dump, pre_dump
from marshmallow_utils.fields import SanitizedHTML, SanitizedUnicode

from zenodo_rdm.legacy.deserializers.schemas import FUNDER_ROR_TO_DOI
from zenodo_rdm.legacy.vocabularies.licenses import rdm_to_legacy


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


class ContributorSchema(CreatorSchema):
    """Contributor schema."""

    type = fields.Method("dump_role")

    def dump_role(self, obj):
        """Loads role field."""
        role = obj.get("role")

        if role:
            # English title matches DataCite prop, used in legacy Zenodo
            return role.get("title", {}).get("en")


class JournalSchema(Schema):
    """Journal schema."""

    title = SanitizedUnicode()
    volume = SanitizedUnicode()
    issue = SanitizedUnicode()
    pages = SanitizedUnicode()


class MeetingSchema(Schema):
    """Meeting schema."""

    title = SanitizedUnicode()
    acronym = SanitizedUnicode()
    dates = SanitizedUnicode()
    place = SanitizedUnicode()
    url = SanitizedUnicode()
    session = SanitizedUnicode()
    session_part = SanitizedUnicode()


class ImprintSchema(Schema):
    """Imprint schema."""

    publisher = SanitizedUnicode()
    isbn = SanitizedUnicode()
    place = SanitizedUnicode()


class PartOfSchema(Schema):
    """'Part of' schema."""

    pages = SanitizedUnicode()
    title = SanitizedUnicode()


class ThesisSchema(Schema):
    """Thesis schema."""

    university = SanitizedUnicode()


class MetadataSchema(Schema):
    """Metadata schema."""

    title = SanitizedUnicode()
    publication_date = SanitizedUnicode()
    description = SanitizedHTML()
    creators = fields.List(fields.Nested(CreatorSchema), dump_only=True)
    grants = fields.Method("dump_grants")

    license = fields.Method("dump_license")

    contributors = fields.List(fields.Nested(ContributorSchema), dump_only=True)

    journal = fields.Nested(JournalSchema, attribute="custom_fields.journal:journal")

    meeting = fields.Nested(MeetingSchema, attribute="custom_fields.meeting:meeting")

    imprint = fields.Nested(ImprintSchema, attribute="custom_fields.imprint:imprint")

    part_of = fields.Nested(PartOfSchema, data_key="part_of")

    thesis = fields.Nested(ThesisSchema, attribute="custom_fields.thesis:university")

    @pre_dump
    def hook_contributors_thesis(self, data, **kwargs):
        """Hooks university key to thesis."""
        university = data.get("custom_fields").get("thesis:university")
        if university:
            new_thesis = {"university": university}
            data["custom_fields"]["thesis:university"] = new_thesis
        return data

    @pre_dump
    def hook_imprint_partof(self, data, **kwargs):
        """Hooks imprint and part_of. fields."""
        # custom_fields.imprint:imprint was already the attribute of another field.
        imprint = data.get("custom_fields", {}).get("imprint:imprint")
        publisher = data.get("publisher")
        if imprint:
            data["part_of"] = imprint
        if publisher:
            data["custom_fields"]["imprint:imprint"] = {
                **imprint,
                "publisher": publisher,
            }
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

    def _funder(self, funder):
        """Serialize RDM funder into Zenodo legacy funder."""
        legacy_funder = {"name": funder["name"]}

        for identifier in funder.get("identifiers"):
            scheme = identifier["scheme"]

            if scheme == "doi":
                legacy_funder["doi"] = identifier["identifier"]

        value = funder.get("country")
        if value:
            legacy_funder["country"] = value

        return legacy_funder

    def _award(self, award):
        """Serialize an RDM award into a legacy Zenodo grant."""
        funder_ror = award["funder"]["id"]
        funder_doi_or_ror = FUNDER_ROR_TO_DOI.get(funder_ror, funder_ror)
        legacy_grant = {
            "code": award["number"],
            "internal_id": f"{funder_doi_or_ror}::{award['id']}",
        }

        try:
            title = award["title"].get("en", next(iter(award["title"])))
            legacy_grant["title"] = title
        except StopIteration:
            pass

        value = award.get("acronym")
        if value:
            legacy_grant["acronym"] = value

        for identifier in award.get("identifiers"):
            scheme = identifier["scheme"]

            if scheme == "url":
                legacy_grant["url"] = identifier["identifier"]

            if scheme == "doi":
                legacy_grant["doi"] = identifier["doi"]

        return legacy_grant

    def dump_grants(self, obj):
        """Dump grants from funding field."""
        funding = obj.get("funding")
        if not funding:
            return missing

        for funding_item in funding:
            award = funding_item.get("award")

            # in case there are multiple funding entries, service calls could be
            # optimized calling read_many
            aid = award.get("id")
            if aid:
                a_service = current_service_registry.get("awards")
                try:
                    award = a_service.read(system_identity, aid).to_dict()
                except (PIDDeletedError, PIDDoesNotExistError):
                    # funder only funding, or custom awards are not supported in the
                    # legacy API
                    return missing

            # we are ignoring funding.funder.id in favour of the awards.funder.id
            fid = award["funder"]["id"]
            f_service = current_service_registry.get("funders")
            # every vocabulary award must be linked to a vocabulary funder
            # therefore this read call cannot fail
            funder = f_service.read(system_identity, fid).to_dict()

            # No custom funder/awards in legacy therefore it would always resolve
            # the read ops above.
            legacy_grant = self._award(award)
            legacy_grant["funder"] = self._funder(funder)

            return legacy_grant

    def dump_license(self, data):
        """Dumps license field."""
        license = data.get("rights", [])

        if not license:
            return missing

        # Zenodo legacy only accepts one right.
        license = license[0]

        legacy_id = rdm_to_legacy(license["id"])
        legacy_license = {"id": legacy_id}

        return legacy_license

    @post_dump(pass_original=True)
    def dump_notes(self, result, original, **kwargs):
        """Dump notes."""
        additional_descriptions = original.get("additional_descriptions", [])
        notes = "".join([ad.get("description", "") for ad in additional_descriptions])
        if notes:
            result["notes"] = notes
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

    @pre_dump
    def hook_metadata_custom_fields(self, data, **kwargs):
        """Hooks 'custom_fields' to 'metadata.custom_fields'."""
        data["metadata"]["custom_fields"] = data.get("custom_fields")
        return data

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
