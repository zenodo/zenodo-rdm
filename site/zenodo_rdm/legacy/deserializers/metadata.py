# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Metadata schemas."""
from datetime import date

import pycountry
from flask import current_app
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    missing,
    post_load,
    pre_load,
    validates_schema,
)
from marshmallow_utils.fields import SanitizedUnicode
from marshmallow_utils.schemas import IdentifierSchema
from nameparser import HumanName
from werkzeug.local import LocalProxy

from ..vocabularies.licenses import LEGACY_LICENSES, legacy_to_rdm

record_identifiers_schemes = LocalProxy(
    lambda: current_app.config["RDM_RECORDS_IDENTIFIERS_SCHEMES"]
)

# based on
# DOI to id https://digital-repositories.web.cern.ch/zenodo/support/operations/#openaire-grants-import
# id to ROR: https://github.com/inveniosoftware/invenio-vocabularies/blob/master/invenio_vocabularies/config.py#L64
FUNDER_DOI_TO_ROR = {
    "10.13039/501100001665": "00rbzpz17",
    "10.13039/501100002341": "05k73zm37",
    "10.13039/501100000923": "05mmh0f86",
    "10.13039/100018231": "03zj4c476",
    "10.13039/501100000024": "01gavpb45",
    "10.13039/501100000780": "00k4n6c32",
    "10.13039/501100000806": "02k4b9v70",
    "10.13039/501100001871": "00snfqn58",
    "10.13039/501100002428": "013tf3c58",
    "10.13039/501100004488": "03n51vw80",
    "10.13039/501100004564": "01znas443",
    "10.13039/501100000925": "011kf5r70",
    "10.13039/100000002": "01cwqze88",
    "10.13039/501100000038": "01h531d29",
    "10.13039/100000001": "021nxhr62",
    "10.13039/501100003246": "04jsz6e67",
    # NOTE: RCUK was succeeded by UKRI. All awards/grants were transferred, so
    #       we're also remapping the funder IDs to point to UKRI (001aqnf71)
    "10.13039/501100000690": "001aqnf71",
    "10.13039/100014013": "001aqnf71",
    "10.13039/501100001602": "0271asj38",
    "10.13039/501100001711": "00yjd3n13",
    "10.13039/100001345": "006cvnv84",
    "10.13039/501100004410": "04w9kkr77",
    "10.13039/100004440": "029chgv08",
    "10.13039/501100006364": "03m8vkq32",
}

FUNDER_ROR_TO_DOI = {v: k for k, v in FUNDER_DOI_TO_ROR.items()}


class PersonSchema(Schema):
    """Creator/contributor common person schema."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    type = fields.Constant("personal")
    family_name = SanitizedUnicode()
    given_name = SanitizedUnicode()
    identifiers = fields.List(fields.Dict())

    @post_load(pass_original=True)
    def load_names(self, result, original, **kwargs):
        """Loads given and family name."""
        name = original.get("name")

        if name:
            human_name = HumanName(name)
            result["given_name"] = human_name.first
            result["family_name"] = human_name.surnames

        return result

    @post_load(pass_original=True)
    def load_identifiers(self, result, original, **kwargs):
        """Loads identifiers."""
        identifiers = []

        orcid = original.get("orcid")
        gnd = original.get("gnd")

        if orcid:
            identifiers.append({"scheme": "orcid", "identifier": orcid})
        if gnd:
            identifiers.append({"scheme": "gnd", "identifier": gnd})

        if identifiers:
            result["identifiers"] = identifiers

        return result


class CreatorSchema(Schema):
    """Creator schema."""

    class Meta:
        """Meta class."""

        unknown = EXCLUDE

    person_or_org = fields.Nested(PersonSchema)
    affiliations = fields.List(fields.Dict())

    @pre_load
    def hook_person_or_org(self, data, **kwargs):
        """Hooks fields to person_or_org."""
        data["person_or_org"] = {
            "name": data.get("name"),
            "orcid": data.get("orcid"),
            "gnd": data.get("gnd"),
        }
        return data

    @post_load(pass_original=True)
    def load_affiliations(self, result, original, **kwargs):
        """Loads affiliation."""
        affiliation = original.get("affiliation")

        if affiliation:
            result["affiliations"] = [{"name": affiliation}]

        return result


class ReferenceSchema(Schema):
    """Reference schema."""

    reference = SanitizedUnicode()


class MetadataSchema(Schema):
    """Transform the metadata of a record."""

    class Meta:
        """Meta attributes for the schema."""

        unknown = EXCLUDE

    # TODO add later
    # if not data:
    #     raise ValidationError("Empty metadata is not accepted")

    @pre_load
    def split_identifiers(self, data, **kwargs):
        """Splits alternate and related identifiers."""
        # Some identifiers are alternate identifiers if the relation is "isAlternateIdentifier"
        input_identifiers = data.get("related_identifiers", [])
        alternate_identifiers = []
        related_identifiers = []
        for identifier in input_identifiers:
            if identifier.get("relation", "") == "isAlternateIdentifier":
                alternate_identifiers.append(identifier)
            else:
                related_identifiers.append(identifier)

        if related_identifiers:
            data["related_identifiers"] = related_identifiers
        if alternate_identifiers:
            data["alternate_identifiers"] = alternate_identifiers

        return data

    title = SanitizedUnicode()
    description = SanitizedUnicode()
    publication_date = SanitizedUnicode(load_default=lambda: date.today().isoformat())
    resource_type = fields.Str()
    creators = fields.List(fields.Nested(CreatorSchema))
    publisher = fields.Constant("Zenodo")  # TODO is it?
    funding = fields.Method(deserialize="load_funding", data_key="grants")
    rights = fields.Method(deserialize="load_rights", data_key="license")
    contributors = fields.List(fields.Dict())
    additional_descriptions = fields.List(fields.Dict())
    locations = fields.Method(deserialize="load_locations")
    subjects = fields.List(fields.Dict())
    version = SanitizedUnicode()
    dates = fields.Method(deserialize="load_dates")
    references = fields.Method(deserialize="load_references")
    language = fields.Method(deserialize="load_language")
    related_identifiers = fields.Method(deserialize="load_related_identifiers")
    identifiers = fields.Method(deserialize="load_alternate_identifiers")

    @post_load(pass_original=True)
    def load_upload_type(self, result, original, **kwargs):
        """Loads upload type."""
        t = original.get("upload_type")
        if t:
            st = original.get(f"{t}_type")
            upload_type = {"id": f"{t}-{st}"} if st else {"id": t}
            result["resource_type"] = upload_type
        return result

    def load_funding(self, obj):
        """Loads funding."""
        _funding = []
        grants = obj

        if not grants:
            return missing

        for grant in grants:
            # format "10.13039/501100000780::190101904"
            id_parts = grant["id"].split("::", 1)
            assert len(id_parts) == 2

            # special case of funder loaded in Zenodo with no DOI related to it.
            # it is part of the vocabulary.
            funder_doi = id_parts[0]
            award_id = id_parts[1]
            funder_doi_or_ror = FUNDER_DOI_TO_ROR.get(funder_doi, funder_doi)

            _funding.append(
                {
                    "funder": {"id": funder_doi_or_ror},
                    "award": {"id": f"{funder_doi_or_ror}::{award_id}"},
                }
            )
        return _funding

    @post_load(pass_original=True)
    def load_contributors(self, result, original, **kwargs):
        """Load contributors from Zenodo."""
        creator_schema = CreatorSchema()
        # Will return a list of contributors + supervisors
        ret = []

        # Process supervisors
        thesis_supervisors = original.get("thesis_supervisors", [])
        if thesis_supervisors:
            for supervisor in thesis_supervisors:
                serialized_sv = creator_schema.load(supervisor)
                serialized_sv["role"] = {"id": "supervisor"}
                ret.append(serialized_sv)

        # Process contributors
        contributors = original.get("contributors", [])
        for c in contributors:
            contributor = creator_schema.load(c)
            type = c.get("type")
            if type:
                # Zenodo role matches ZenodoRDM ids, lower cased
                contributor["role"] = {"id": type.lower()}
            ret.append(contributor)

        if ret:
            result["contributors"] = ret

        return result

    def load_rights(self, obj):
        """Loads rights."""
        rdm_license = legacy_to_rdm(obj)

        ret = {}
        if rdm_license:
            ret = {"id": rdm_license}
        else:
            # If license does not exist in RDM, it is added as custom
            legacy_license = LEGACY_LICENSES.get(obj)
            ret = {"title": {"en": legacy_license["title"]}}

        return [ret]

    @post_load(pass_original=True)
    def load_additional_descriptions(self, result, original, **kwargs):
        """Transform notes of a legacy record."""
        rdm_additional_descriptions = []

        notes = original.get("notes")
        if notes:
            rdm_additional_descriptions.append(
                {"description": notes, "type": {"id": "other"}}
            )

        method = original.get("method")
        if method:
            rdm_additional_descriptions.append(
                {"description": method, "type": {"id": "methods"}}
            )

        if rdm_additional_descriptions:
            result["additional_descriptions"] = rdm_additional_descriptions

        return result

    def load_locations(self, obj):
        """Transform locations of a legacy record."""
        features = []
        for legacy_location in obj:
            lat = legacy_location.get("lat")
            lon = legacy_location.get("lon")
            place = legacy_location["place"]
            description = legacy_location.get("description")

            feature = {"place": place}

            if lat and lon:
                geometry = {"type": "Point", "coordinates": [lon, lat]}
                feature.update({"geometry": geometry})

            if description:
                feature.update({"description": description})

            features.append(feature)

        return {"features": features}

    @post_load(pass_original=True)
    def _subjects(self, result, original, **kwargs):
        """Transform subjects of a legacy record.

        RDM subjects translate to either legacy keywords or subjects.
        """

        def _from_keywords(keywords):
            """Legacy keywords are free text strings.

            They map to custom subjects.
            """
            return [{"subject": kw} for kw in keywords]

        def _from_subjects(data):
            """Maps RDM subjects to legacy subjects.

            Legacy subjects are custom vocabularies.
            """
            # TODO we still did not define a strategy to map legacy subjects to rdm.
            return []

        keywords = original.get("keywords", [])
        subjects = original.get("subjects", [])

        if keywords or subjects:
            rdm_subjects = _from_keywords(keywords) + _from_subjects(subjects)

            result["subjects"] = rdm_subjects

        return result

    def load_dates(self, obj):
        """Transform dates of a legacy record."""
        rdm_dates = []

        for legacy_date in obj:
            start_date = legacy_date.get("start")
            end_date = legacy_date.get("end")
            description = legacy_date.get("description")
            rdm_date = None
            if start_date and end_date:
                rdm_date = f"{start_date}/{end_date}"
            else:
                # RDM implements EDTF Level 0. Open intervals are not allowed
                raise ValidationError("Invalid date provided.")

            rdm_date = {
                "date": rdm_date,
                # Type is required on legacy Zenodo
                "type": {
                    # Type is a vocabulary on ZenodoRDM.
                    "id": legacy_date["type"].lower(),
                },
            }

            if description:
                rdm_date.update({"description": description})
            rdm_dates.append(rdm_date)

        return rdm_dates

    def load_references(self, obj):
        """Transform references of a legacy record."""
        rdm_references = []

        for legacy_reference in obj:
            _rdm_reference = {"reference": legacy_reference}
            rdm_references.append(_rdm_reference)

        return rdm_references

    def load_language(self, obj):
        """Transform language of a legacy record."""

        def _map_iso_639_1_to_639_2(language):
            """Maps ISO 639-1 (2 digits) to ISO 639-2 (3 digits).

            RDM implements 639-3 (3 digits), which is an extension of 639-2.
            Therefore, mapping from 639-1 to 639-2 should be enough.

            See: https://www.loc.gov/standards/iso639-2/php/code_list.php
            """
            mapping = pycountry.languages.get(alpha_2=language)
            if mapping:
                return mapping.alpha_3

            return None

        language = None

        # Case 1 - 3 letter code
        if len(obj) == 3:
            language = obj
        # Case 2  - 2 letter code
        elif len(obj) == 2:
            language = _map_iso_639_1_to_639_2(obj)
        else:
            raise ValidationError(
                "Language must be either ISO-639-1 or 639-2 compatible."
            )

        return [{"id": language}]

    def load_related_identifiers(self, obj):
        """Transform related identifiers of a legacy record."""
        related_identifiers = []
        identifier_schema = IdentifierSchema(allowed_schemes=record_identifiers_schemes)
        for legacy_identifier in obj:
            # Identifier schema is used to detect the identifier's 'scheme'.
            # In legacy, 'scheme' is not passed as a parameter. Instead, it's detected from the identifier itself.

            # Patches a typo legacy relation type (see https://github.com/zenodo/zenodo/issues/1366)
            if legacy_identifier["relation"] == "isOrignialFormOf":
                legacy_identifier["relation"] = "isOriginalFormOf"

            identifier = identifier_schema.load(
                {
                    "identifier": legacy_identifier["identifier"],
                }
            )
            rdm_identifier = {
                **identifier,
                "relation_type": {
                    # relation_type is a vocabulary
                    "id": legacy_identifier["relation"].lower(),
                },
            }

            # Resource type is optional.
            legacy_type = legacy_identifier.get("resource_type")
            if legacy_type:
                rdm_identifier.update({"resource_type": {"id": legacy_type}})

            related_identifiers.append(rdm_identifier)

        return related_identifiers

    def load_alternate_identifiers(self, obj):
        """Transform alternate identifiers of a legacy record."""
        alternate_identifiers = []
        identifier_schema = IdentifierSchema(allowed_schemes=record_identifiers_schemes)

        for legacy_identifier in obj:
            rdm_identifier = identifier_schema.load(
                {
                    "identifier": legacy_identifier["identifier"],
                }
            )

            alternate_identifiers.append(rdm_identifier)

        return alternate_identifiers

    @validates_schema
    def validate_metadata_schema(self, data, **kwargs):
        """Validates metadata schema."""
        keys = list(data.keys())

        # Publisher is hardcoded to "Zenodo".
        if len(keys) == 1 and keys[0] == "publisher":
            raise ValidationError("Metadata must be non-empty")
