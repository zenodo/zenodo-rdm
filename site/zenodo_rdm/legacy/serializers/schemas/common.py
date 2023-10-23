# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo common serializer schemas."""

from invenio_communities.communities.services.service import get_cached_community_slug
from invenio_communities.proxies import current_communities
from marshmallow import Schema, fields, missing, post_dump, pre_dump
from marshmallow_utils.fields import EDTFDateString, SanitizedHTML, SanitizedUnicode
from zenodo_legacy.funders import FUNDER_ACRONYMS, FUNDER_ROR_TO_DOI
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
    "isalternateidentifier": "isAlternateIdentifier",
}


class CreatorSchema(Schema):
    """Creator schema."""

    name = SanitizedUnicode(
        attribute="person_or_org.name"
    )  # TODO rdm name is different than legacy zenodo
    affiliation = fields.Method("dump_affiliation")

    def dump_affiliation(self, obj):
        """Dump affiliation."""
        if obj.get("affiliations"):
            return obj["affiliations"][0].get("name")

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
    type = SanitizedUnicode(attribute="type.id")
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

    access_right = fields.Method("dump_access_right")
    embargo_date = fields.String(attribute="access.embargo.until")

    creators = fields.List(fields.Nested(CreatorSchema), dump_only=True)
    contributors = fields.List(fields.Nested(ContributorSchema), dump_only=True)

    keywords = fields.Method("dump_keywords")
    subjects = fields.Raw(attribute="custom_fields.legacy:subjects")

    related_identifiers = fields.List(fields.Nested(RelatedIdentifierSchema))

    locations = fields.Method("dump_locations")
    dates = fields.List(fields.Nested(DateSchema))

    version = SanitizedUnicode()

    references = fields.Method("dump_reference")
    language = fields.Method("dump_languages")

    @pre_dump
    def resolve_communities(self, data, **kwargs):
        """Resolve communities for the draft/record."""
        community_slugs = set()

        # Check draft communities
        draft_communities = data.get("custom_fields", {}).get("legacy:communities", [])
        if draft_communities:
            community_slugs |= set(draft_communities)
        # Check parent communities
        parent_communities = (
            data.get("parent", {}).get("communities", {}).get("ids", [])
        )
        service_id = current_communities.service.id
        for community_id in parent_communities:
            try:
                slug = get_cached_community_slug(
                    community_id, service_id, cache_ttl=60 * 60 * 24
                )
                community_slugs.add(slug)
            except Exception:
                pass
        if community_slugs:
            data["_communities"] = community_slugs
        return data

    @pre_dump
    def resolve_license(self, data, **kwargs):
        """Resolve communities for the draft/record."""
        license = data.get("rights", [])
        if license:
            # Zenodo legacy only accepts one license.
            license = license[0]
            data["license"] = rdm_to_legacy(license["id"])
        return data

    def dump_keywords(self, obj):
        """Dumps keywords from RDM subjects."""
        subjects = obj.get("subjects", [])
        serialized_keywords = []
        if subjects:
            for _sbj in subjects:
                _id = _sbj.get("id")
                _subject = _sbj.get("subject")
                # If subject has an id, it's a controlled vocabulary
                if _id:
                    pass
                # Otherwise it's a free text string (keyword)
                elif _subject:
                    serialized_keywords.append(_subject)

        return serialized_keywords or missing

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

    def _grant(self, award, funder):
        """Serialize an RDM award and funder into a legacy Zenodo grant."""
        # RDM allows specifying only funder
        if not award:
            return
        funder_id = funder.get("id")
        funder_id = FUNDER_ROR_TO_DOI.get(funder_id, funder_id)
        award_number = award.get("number")
        if not (funder_id and award_number):
            return

        grant = {
            "code": award_number,
            "internal_id": f"{funder_id}::{award_number}",
            "funder": {"name": funder["name"]},
        }

        # Add more funder fields
        for identifier in funder.get("identifiers", []):
            scheme = identifier["scheme"]
            if scheme == "doi":
                grant["funder"]["doi"] = identifier["identifier"]
        if "doi" not in grant["funder"] and funder_id.startswith("10.13039/"):
            grant["funder"]["doi"] = funder_id
        country = funder.get("country")
        if country:
            grant["funder"]["country"] = country
        acronym = FUNDER_ACRONYMS.get(funder_id) or funder.get("acronym")
        if acronym:
            grant["funder"]["acronym"] = acronym

        # Add more award fields
        i18n_title = award.get("title") or {}
        title = i18n_title.get("en") or next(iter(i18n_title.values()), None)
        if title:
            grant["title"] = title

        for key in ("acronym", "program"):
            value = award.get(key)
            if value:
                grant[key] = value

        for identifier in award.get("identifiers", []):
            scheme = identifier["scheme"]
            if scheme == "url":
                grant["url"] = identifier["identifier"]
            if scheme == "doi":
                grant["doi"] = identifier["doi"]
        return grant

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

    @pre_dump
    def hook_metadata(self, data, **kwargs):
        """Hooks up top-level fields under metadata."""
        data.setdefault("metadata", {})
        data["metadata"]["custom_fields"] = data.get("custom_fields")
        data["metadata"]["access"] = data["access"]
        data["metadata"]["pids"] = data.get("pids")
        data["metadata"]["parent"] = data.get("parent")
        data["metadata"]["versions"] = data.get("versions")
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
