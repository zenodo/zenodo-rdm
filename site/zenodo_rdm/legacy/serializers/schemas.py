# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy serializer schemas."""

from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError
from invenio_records_resources.proxies import current_service_registry
from marshmallow import Schema, fields, missing, post_dump, pre_dump, validate
from marshmallow_utils.fields import EDTFDateString, SanitizedHTML, SanitizedUnicode
from zenodo_legacy.funders import FUNDER_ROR_TO_DOI
from zenodo_legacy.licenses import rdm_to_legacy


def to_camel_case(string, split_char=" "):
    """Returns a camel cased string."""
    return "".join(word.title() for word in string.split(split_char))


# Maps RDM relation_type to legacy relation
RELATION_TYPE_MAPPING = {
    "iscitedby": "isCitedBy",
    "cites": "cites",
    "issupplementto": "isSupplementTo",
    "issupplementedby": "isSupplementedBy",
    "iscontinuedby": "isContinuedBy",
    "continues": "continues",
    "isdescribedby": "isDescribedBy",
    "describes": "describes",
    "hasmetadata": "hasMetadata",
    "ismetadatafor": "isMetadataFor",
    "hasversion": "hasVersion",
    "isversionof": "isVersionOf",
    "isnewversionof": "isNewVersionOf",
    "ispreviousversionof": "isPreviousVersionOf",
    "ispartof": "isPartOf",
    "haspart": "hasPart",
    "ispublishedin": "isPublishedIn",
    "isreferencedby": "isReferencedBy",
    "references": "references",
    "isdocumentedby": "isDocumentedBy",
    "documents": "documents",
    "iscompiledby": "isCompiledBy",
    "compiles": "compiles",
    "isvariantformof": "isVariantFormOf",
    "isoriginalformof": "isOriginalFormOf",
    "isidenticalto": "isIdenticalTo",
    "isreviewedby": "isReviewedBy",
    "reviews": "reviews",
    "isderivedfrom": "isDerivedFrom",
    "issourceof": "isSourceOf",
    "isrequiredby": "isRequiredBy",
    "requires": "requires",
    "isobsoletedby": "isObsoletedBy",
    "obsoletes": "obsoletes",
}


class FileSchema(Schema):
    """File schema."""

    key = SanitizedUnicode()
    size = fields.Number()
    checksum = SanitizedUnicode()


class CreatorSchema(Schema):
    """Creator schema."""

    name = SanitizedUnicode(
        attribute="person_or_org.name"
    )  # TODO rdm name is different than legacy zenodo
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
                _id = i["identifier"]
                if i["scheme"] == "orcid":
                    result["orcid"] = _id.replace("orcid:", "")
                if i["scheme"] == "gnd":
                    result["gnd"] = _id.replace("gnd:", "")
        return result


class ContributorSchema(CreatorSchema):
    """Contributor schema."""

    type = fields.Method("dump_role")

    def dump_role(self, obj):
        """Loads role field."""
        # English title matches DataCite prop, used in legacy Zenodo
        role = obj.get("role", {})
        if role:
            title_en = role.get("title", {}).get("en")
            return to_camel_case(title_en, " ")


class DateSchema(Schema):
    """Date schema."""

    start = EDTFDateString()
    end = EDTFDateString()
    type = SanitizedUnicode(
        attribute="type.id",
        validate=validate.OneOf(["collected", "valid", "withdrawn"]),
    )
    description = SanitizedUnicode()

    @post_dump(pass_original=True)
    def dump_date(self, result, original, **kwargs):
        """Dumps date field."""
        date = original.get("date")
        if date:
            interval = date.split("/")
            is_interval = len(interval) == 2
            start = None
            end = None
            # EDTF level 0 specifies intervals using "/" (e.g. 2004-02-01/2005-02)
            if is_interval:
                start = interval[0]
                end = interval[1]
                result["start"] = start
                result["end"] = end
            else:
                # RDM implements EDTF level 0. Therefore, no open intervals are allowed.
                # TODO throw an error
                pass

        return result


class RelatedIdentifierSchema(Schema):
    """Related identifier schema."""

    identifier = SanitizedUnicode()
    relation = fields.Method("dump_relation")
    resource_type = SanitizedUnicode(attribute="resource_type.id")
    scheme = SanitizedUnicode()

    def dump_relation(self, obj):
        """Dumps relation type."""
        resource_type_id = obj.get("relation_type", {}).get("id")

        if not resource_type_id:
            return missing

        legacy_relation = RELATION_TYPE_MAPPING.get(resource_type_id)

        # Or throw an error
        return legacy_relation or missing


class MetadataSchema(Schema):
    """Metadata schema."""

    title = SanitizedUnicode()
    doi = SanitizedUnicode(attribute="pids.doi.identifier", dump_only=True)
    publication_date = SanitizedUnicode()
    description = SanitizedHTML()
    creators = fields.List(fields.Nested(CreatorSchema), dump_only=True)
    grants = fields.Method("dump_grants")

    license = fields.Method("dump_license")

    contributors = fields.List(fields.Nested(ContributorSchema), dump_only=True)

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

    locations = fields.Method("dump_locations")

    version = SanitizedUnicode()

    dates = fields.List(fields.Nested(DateSchema))

    references = fields.Method("dump_reference")

    language = fields.Method("dump_languages")

    related_identifiers = fields.List(fields.Nested(RelatedIdentifierSchema))

    access_right = fields.Method("dump_access_right")

    embargo_date = fields.String(attribute="access.embargo.until")

    communities = fields.Method("dump_communities")

    def dump_communities(self, obj):
        """Dump communities."""
        community_slugs = set()

        # Check draft communities
        draft_communities = obj.get("custom_fields", {}).get("legacy:communities", [])
        if draft_communities:
            community_slugs |= set(draft_communities)
        # Check parent communities
        parent_communities = obj.get("parent", {}).get("communities", {}).get("ids", [])
        community_cls = current_communities.service.record_cls
        for community_id in parent_communities:
            # NOTE: This is bery bad, we're performing DB queries for every community ID
            #       in order to resolve the slug required by the legacy API.
            try:
                community = community_cls.pid.resolve(community_id)
                community_slugs.add(community.slug)
            except Exception:
                pass

        return [{"identifier": c} for c in community_slugs] or missing

    @pre_dump
    def hook_alternate_identifiers(self, data, **kwargs):
        """Hooks 'identifiers' into related identifiers."""
        alternate_identifiers = data.get("identifiers", [])
        related_identifiers = data.get("related_identifiers", [])
        for identifier in alternate_identifiers:
            related_identifier = {
                "relation_type": {"id": "isAlternateIdentifier"},
                "identifier": identifier["identifier"],
            }
            related_identifiers.append(related_identifier)
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

    @post_dump(pass_original=True)
    def dump_subjects(self, result, original, **kwargs):
        """Dumps subjects."""
        subjects = original.get("subjects", [])
        serialized_subjects = []
        serialized_keywords = []
        if subjects:
            for _sbj in subjects:
                _id = _sbj.get("id")
                _subject = _sbj.get("subject")
                # If subject has an id, it's a controlled vocabulary
                if _id:
                    # TODO we still did not define a strategy to map legacy subjects to rdm.
                    pass
                # Otherwise it's a free text string (keyword)
                elif _subject:
                    serialized_keywords.append(_subject)

        if serialized_keywords:
            result["keywords"] = serialized_keywords

        if serialized_subjects:
            result["subjects"] = serialized_subjects

        return result

    def dump_reference(self, obj):
        """Dumps reference."""
        references_list = obj.get("references", [])
        if not references_list:
            return missing

        return [_ref["reference"] for _ref in references_list]

    def dump_access_right(self, obj):
        """Dumps access right."""
        access = obj["access"]
        files_access = access["files"]
        is_open = files_access == "public"
        is_embargoed = access.get("embargo", {}).get("active")
        is_restricted = not is_embargoed and files_access == "restricted"

        legacy_access = None

        if is_open:
            legacy_access = "open"
        # TODO access requests still need to be implemented.
        elif is_restricted:
            legacy_access = "restricted"
        elif is_embargoed:
            legacy_access = "embargoed"
        # TODO how to map to closed access?

        if not legacy_access:
            # Throw an error maybe?
            pass

        return legacy_access

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

        ret = []
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

            award_number = award["number"]
            funder_doi = FUNDER_ROR_TO_DOI.get(funder["id"])
            serialized_grant = {"id": f"{funder_doi}::{award_number}"}
            ret.append(serialized_grant)

        return ret

    def dump_license(self, data):
        """Dumps license field."""
        license = data.get("rights", [])

        if not license:
            return missing

        # Zenodo legacy only accepts one right.
        license = license[0]

        legacy_id = rdm_to_legacy(license["id"])
        legacy_license = legacy_id

        return legacy_license

    @post_dump(pass_original=True)
    def dump_additional_descriptions(self, result, original, **kwargs):
        """Dump notes."""
        additional_descriptions = original.get("additional_descriptions", [])

        methods = None
        notes = None
        for ad in additional_descriptions:
            ad_type = ad["type"]["id"]
            if ad_type == "other":
                notes = ad.get("description", "")
            if ad_type == "methods":
                methods = ad.get("description", "")

        if notes:
            result["notes"] = notes
        if methods:
            result["method"] = methods

        return result

    def dump_locations(self, data):
        """Dumps locations fields."""
        locations = data.get("locations")
        if not locations:
            return missing

        # In rdm, features is mandatory
        features = locations["features"]
        legacy_locations = []
        for feature in features:
            legacy_loc = {}

            place = feature.get("place")
            description = feature.get("description")

            if place:
                legacy_loc["place"] = place
            if description:
                legacy_loc["description"] = description

            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates")
            if coordinates:
                # In rmd coordinates have the format [long, lat]
                legacy_loc["lon"] = coordinates[0]
                legacy_loc["lat"] = coordinates[1]
            legacy_locations.append(legacy_loc)

        return legacy_locations

    def dump_languages(self, obj):
        """Dump languages."""
        languages = obj.get("languages", [])

        if not languages:
            return missing

        # Legacy Zenodo accepts either ISO-639-1 or ISO-639-2 codes.
        # Zenodo-RDM implements ISO-639-2 so no mapping is needed.
        return languages[0]["id"]


class LegacySchema(Schema):
    """Legacy schema."""

    created = SanitizedUnicode()
    modified = SanitizedUnicode(attribute="updated")

    id = fields.Integer(dump_only=True)
    record_id = fields.Integer(attribute="id", dump_only=True)
    conceptrecid = SanitizedUnicode(attribute="parent.id", dump_only=True)

    doi = SanitizedUnicode(attribute="pids.doi.identifier", dump_only=True)
    conceptdoi = SanitizedUnicode(
        attribute="parent.pids.doi.identifier",
        dump_only=True,
    )

    doi_url = SanitizedUnicode(attribute="links.doi", dump_only=True)

    metadata = fields.Nested(MetadataSchema, dump_only=True)
    title = SanitizedUnicode(
        attribute="metadata.title", dump_only=True, dump_default=""
    )

    links = fields.Raw(dump_only=True)

    owner = fields.Method("dump_owner", dump_only=True)

    files = fields.Method("dump_files", dump_only=True)

    def dump_owner(self, obj):
        """Dump owner."""
        return obj["parent"]["access"]["owned_by"]["user"]

    def dump_files(self, obj):
        """Dump files."""
        # TODO: pass files via service
        return []

    @pre_dump
    def hook_metadata(self, data, **kwargs):
        """Hooks up top-level fields under metadata."""
        data.setdefault("metadata", {})
        data["metadata"]["custom_fields"] = data.get("custom_fields")
        data["metadata"]["access"] = data["access"]
        data["metadata"]["pids"] = data.get("pids")
        data["metadata"]["parent"] = data.get("parent")
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
        recid = original["id"]
        result["metadata"]["prereserve_doi"] = {
            "doi": f"10.5281/zenodo.{recid}",
            "recid": int(recid),
        }
        return result
