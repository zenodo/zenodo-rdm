# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy deserializer schemas."""

from copy import deepcopy
from datetime import date

import pycountry
from flask import current_app
from invenio_records.dictutils import clear_none
from marshmallow_utils.schemas import IdentifierSchema
from nameparser import HumanName
from werkzeug.local import LocalProxy

from ..vocabularies.licenses import LEGACY_LICENSES, legacy_to_rdm
from ..vocabularies.utils import _load_json

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
    "10.13039/100018231": "01gavpb45",
    "10.13039/501100000024": "00k4n6c32",
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
    "10.13039/501100000690": "10.13039/501100000690",
    "10.13039/100014013": "001aqnf71",
    "10.13039/501100001602": "0271asj38",
    "10.13039/501100001711": "00yjd3n13",
    "10.13039/100001345": "006cvnv84",
    "10.13039/501100004410": "04w9kkr77",
    "10.13039/100004440": "029chgv08",
    "10.13039/501100006364": "03m8vkq32",
    "10.13039/501100000780": "00k4n6c32",
}

FUNDER_ROR_TO_DOI = {v: k for k, v in FUNDER_DOI_TO_ROR.items()}


class LegacyRecordTransform:
    """Transform a Zenodo legacy record to an RDM record."""

    def _resource_type(self, data):
        t = data.get("upload_type")
        if t:
            st = data.get(f"{t}_type")
            return {"id": f"{t}-{st}"} if st else {"id": t}

    def _creators(self, data):
        ret = []
        for c in data:
            creator = self._creator(c)
            ret.append(creator)
        return ret

    def _creator(self, data):
        """Deserialize one creator."""
        r = {"person_or_org": {"type": "personal"}}
        if data.get("affiliation"):
            r["affiliations"] = [{"name": data["affiliation"]}]

        identifiers = []
        if data.get("orcid"):
            identifiers.append({"scheme": "orcid", "identifier": data["orcid"]})
        if data.get("gnd"):
            identifiers.append({"scheme": "gnd", "identifier": data["gnd"]})

        if identifiers:
            r["person_or_org"]["identifiers"] = identifiers

        name = HumanName(data["name"])
        r["person_or_org"]["given_name"] = name.first
        r["person_or_org"]["family_name"] = name.surnames
        return r

    def _contributors(self, data):
        """Load contributors from Zenodo."""
        if not data:
            return None

        supervisors = data.get("thesis", {}).get("supervisors", [])
        if supervisors:
            for supervisor in supervisors:
                supervisor["type"] = "Supervisor"
        contributors = data.get("contributors", [])
        contributors.extend(supervisors)

        ret = []
        for c in contributors:
            contributor = self._creator(c)
            type = c.get("type")
            if type:
                # Zenodo role matches ZenodoRDM ids, lower cased
                contributor["role"] = {"id": type.lower()}
            ret.append(contributor)

        return ret

    def _funding(self, grants):
        """Transform funding information."""
        _funding = []
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

    def _rights(self, data):
        """Transform rights (licenses)."""
        if not data:
            return None

        rdm_license = legacy_to_rdm(data)

        ret = {}
        if rdm_license:
            ret = {"id": rdm_license}
        else:
            # If license does not exist in RDM, it is added as custom
            legacy_license = LEGACY_LICENSES.get(data)
            ret = {"title": {"en": legacy_license["title"]}}

        return [ret]

    def _custom_fields(self, data):
        """Transform metadata into custom fields."""

        def _journal(data):
            """Load journal field."""
            if not data:
                return None

            journal_title = data.get("title")
            journal_volume = data.get("volume")
            journal_issue = data.get("issue")
            journal_pages = data.get("pages")

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

            title = data.get("title")
            acronym = data.get("acronym")
            dates = data.get("dates")
            place = data.get("place")
            url = data.get("url")
            session = data.get("session")
            session_part = data.get("session_part")

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

            title = data.get("title")
            pages = data.get("pages")
            isbn = data.get("isbn")
            place = data.get("place")

            rdm_imprint = {
                "title": title,
                "pages": pages,
                "isbn": isbn,
                "place": place,
            }

            clear_none(rdm_imprint)
            return rdm_imprint

        if not data:
            return None

        journal = _journal(data.get("journal"))
        meeting = _meeting(data.get("meeting"))
        imprint = _imprint({**data.get("imprint"), **data.get("part_of")})
        university = data.get("thesis", {}).get("university")

        custom_fields = {
            "journal:journal": journal,
            "meeting:meeting": meeting,
            "imprint:imprint": imprint,
            "thesis:university": university,
        }

        clear_none(custom_fields)

        return custom_fields

    def _additional_descriptions(self, data):
        """Transform notes of a legacy record."""
        if not data:
            return None
        rdm_additional_descriptions = []

        notes = data.get("notes")
        if notes:
            rdm_additional_descriptions.append(
                {"description": notes, "type": {"id": "other"}}
            )

        method = data.get("method")
        if method:
            rdm_additional_descriptions.append(
                {"description": method, "type": {"id": "methods"}}
            )

        return rdm_additional_descriptions

    def _locations(self, data):
        """Transform locations of a legacy record."""
        if not data:
            return None

        features = []
        for legacy_location in data:
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

    def _subjects(self, data):
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

        keywords = data.get("keywords", [])
        subjects = data.get("subjects", [])

        if not (keywords or subjects):
            return None

        rdm_subjects = _from_keywords(keywords) + _from_subjects(subjects)

        return rdm_subjects

    def _dates(self, data):
        """Transform dates of a legacy record."""
        if not data:
            return None

        rdm_dates = []

        for legacy_date in data:
            start_date = legacy_date.get("start")
            end_date = legacy_date.get("end")
            description = legacy_date.get("description")
            rdm_date = None
            if start_date and end_date:
                rdm_date = f"{start_date}/{end_date}"
            else:
                # RDM implements EDTF Level 0. Open intervals are not allowed
                # TODO throw an error.
                continue

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

    def _references(self, data):
        """Transform references of a legacy record."""
        if not data:
            return None

        rdm_references = []

        for legacy_reference in data:
            _rdm_reference = {"reference": legacy_reference}
            rdm_references.append(_rdm_reference)

        return rdm_references

    def _language(self, data):
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

        if not data:
            return None

        language = None

        # Case 1 - 3 letter code
        if len(data) == 3:
            language = data
        # Case 2  - 2 letter code
        elif len(data) == 2:
            language = _map_iso_639_1_to_639_2(data)

        return [{"id": language}] if language else None

    def _related_identifiers(self, data):
        """Transform related identifiers of a legacy record."""
        if not data:
            return None

        related_identifiers = []
        identifier_schema = IdentifierSchema(allowed_schemes=record_identifiers_schemes)
        for legacy_identifier in data:
            # Identifier schema is used to detect the identifier's 'scheme'.
            # In legacy, 'scheme' is not passed as a parameter. Instead, it's detected from the identifier itself.
            # TODO schema.load() might error (e.g. invalid identifier scheme).
            # TODO question: should fields error? They're "ignoring" errors for now (E.g. returning 'None')

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

    def _alternate_identifiers(self, data):
        """Transform alternate identifiers of a legacy record."""
        if not data:
            return None

        alternate_identifiers = []
        identifier_schema = IdentifierSchema(allowed_schemes=record_identifiers_schemes)

        for legacy_identifier in data:
            rdm_identifier = identifier_schema.load(
                {
                    "identifier": legacy_identifier["identifier"],
                }
            )

            alternate_identifiers.append(rdm_identifier)

        return alternate_identifiers

    def _metadata(self, data):
        """Transform the metadata of a record."""

        def _pre_load(data):
            # Some identifiers are alternate identifiers if the relation is "isAlternateIdentifier"
            input_identifiers = data.get("related_identifiers", [])
            alternate_identifiers = []
            related_identifiers = []
            for identifier in input_identifiers:
                if identifier.get("relation", "") == "isAlternateIdentifier":
                    alternate_identifiers.append(identifier)
                else:
                    related_identifiers.append(identifier)

            data["related_identifiers"] = related_identifiers
            data["alternate_identifiers"] = alternate_identifiers

            return data

        original = deepcopy(data)
        data = _pre_load(original)

        if data:
            return {
                "title": data.get("title"),
                "description": data.get("description"),
                "publication_date": data.get(
                    "publication_date",
                    date.today().isoformat(),
                ),
                "resource_type": self._resource_type(data),
                "creators": self._creators(data.get("creators", [])),
                # NOTE: Hardcoded for DataCite
                "publisher": "Zenodo",
                "funding": self._funding(data.get("grants", [])),
                "rights": self._rights(data.get("license")),
                "contributors": self._contributors(data),
                "additional_descriptions": self._additional_descriptions(
                    {"notes": data.get("notes"), "method": data.get("method")}
                ),
                "locations": self._locations(data.get("locations")),
                "subjects": self._subjects(data),
                "version": data.get("version"),
                "dates": self._dates(data.get("dates", [])),
                "references": self._references(data.get("references", [])),
                "languages": self._language(data.get("language")),
                "related_identifiers": self._related_identifiers(
                    data.get("related_identifiers", [])
                ),
                "identifiers": self._alternate_identifiers(
                    data.get("alternate_identifiers", [])
                ),
            }

    def _access(self, data):
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
        metadata = data.get("metadata", {})
        access_right = metadata.get("access_right")
        embargo_date = metadata.get("embargo_date")

        if not access_right:
            # By default records are open access.
            return _open_record()

        is_embargoed = access_right == "embargoed"
        is_restricted = access_right == "restricted"
        is_open = access_right == "open"
        is_closed = access_right == "closed"

        if is_open:
            access = _open_record()
        elif is_restricted or is_closed:
            # TODO access conditions are not yet implemented
            access = _restricted_record()
        elif is_embargoed and embargo_date:
            access = _embargoed_record(embargo_date)

        if not access:
            # TODO throw an error.
            pass

        return access

    def _pids(self, data):
        """Transform legacy doi in RDM pid with external provider."""
        metadata = data.get("metadata")
        doi = metadata.get("doi")

        if not doi:
            return None

        provider = "external"

        if doi.startswith("10.5281/"):
            provider = "datacite"

        rdm_external_pid = {"doi": {"identifier": doi, "provider": provider}}

        return rdm_external_pid

    def load(self, data):
        """Transform data."""
        if not data:
            return {}

        return {
            "metadata": self._metadata(data.get("metadata")),
            "custom_fields": self._custom_fields(data.get("metadata")),
            # TODO: Map old access rights to RDM access
            "access": self._access(data),
            "files": {"enabled": True},
            "pids": self._pids(data),
        }
