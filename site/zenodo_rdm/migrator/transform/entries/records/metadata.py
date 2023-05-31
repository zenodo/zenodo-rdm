# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator metadata entry transformer."""

from urllib.parse import urlparse

from idutils import detect_identifier_schemes
from invenio_rdm_migrator.transform import Entry, drop_nones
from nameparser import HumanName

from zenodo_rdm.legacy.deserializers.metadata import FUNDER_DOI_TO_ROR
from zenodo_rdm.legacy.vocabularies.licenses import LEGACY_LICENSES, legacy_to_rdm

from ....errors import InvalidIdentifier


class ZenodoRecordMetadataEntry(Entry):
    """Metadata entry transform."""

    @classmethod
    def _person_or_org(cls, creatibutor):
        """Parse the person or organization.

        It can be part of a creator, contributor or thesis supervisor.
        """
        r = {"type": "personal"}
        if creatibutor.get("orcid"):
            r["identifiers"] = [
                {"scheme": "orcid", "identifier": creatibutor["orcid"]},
            ]
        name = HumanName(creatibutor["name"])
        r["given_name"] = name.first
        r["family_name"] = name.surnames
        # autocompleted by RDM Metadata schema
        r["name"] = f"{name.surnames}, {name.first}"

        return r

    @classmethod
    def _creatibutor(cls, creatibutor):
        """Parses a creatibutor (person or org and affiliation)."""
        r = {"person_or_org": cls._person_or_org(creatibutor)}
        if creatibutor.get("affiliation"):
            r["affiliations"] = [{"name": creatibutor["affiliation"]}]

        return r

    @classmethod
    def _creators(cls, creators):
        """Parses creators."""
        return [cls._creatibutor(c) for c in creators]

    @classmethod
    def _resource_type(cls, resource_type):
        """Parses resource types."""
        t = resource_type["type"]
        st = resource_type.get("subtype")

        return {"id": f"{t}-{st}"} if st else {"id": t}

    @classmethod
    def _contributors(cls, contributors):
        """Parses contributors."""
        ret = []
        for contributor in contributors:
            r = cls._creatibutor(contributor)
            r["role"] = {"id": contributor["type"].lower()}
            ret.append(r)

        return ret

    @classmethod
    def _supervisors(cls, supervisors):
        """Parses supervisors as contributors with fixed role."""
        ret = []
        for supervisor in supervisors:
            r = cls._creatibutor(supervisor)
            r["role"] = {"id": "supervisor"}
            ret.append(r)

        return ret

    @classmethod
    def _rights(cls, license):
        """Parses rights from license."""
        if not license:
            return None

        # Legacy license is stored like: '{"$ref": "https://dx.zenodo.org/licenses/other-open"}'
        right_ref = license.get("$ref")
        legacy_license = right_ref.split("/")[-1]
        rdm_right = legacy_to_rdm(legacy_license)

        if rdm_right:
            right = {"id": rdm_right}
        else:
            # If the license does not exist in RDM, add it as a custom license.
            right_title = LEGACY_LICENSES.get(legacy_license, {}).get("title", "")
            right = {"title": {"en": right_title}}

        return [right]

    @classmethod
    def _additional_descriptions(cls, note):
        """Parses additional descriptions from notes."""
        if not note:
            return None

        additional_description = {
            "description": note,
            "type": {
                "id": "other",
            },
        }

        return [additional_description]

    @classmethod
    def _languages(cls, language):
        """Parses language from zenodo."""
        if not language:
            return None

        lang = {"id": language}

        return [lang]

    @classmethod
    def _subjects(cls, keywords):
        """Parses subjects from zenodo keywords."""
        if not keywords:
            return None

        ret = []

        for kw in keywords:
            ret.append({"subject": kw})

        return ret

    @classmethod
    def _validate_identifier(cls, identifier):
        """Validates the information of an identifier and completes it if needed."""
        value = identifier.get("identifier", "")
        scheme = identifier.get("scheme")
        if not scheme:
            guess = detect_identifier_schemes(value)
            if guess:
                identifier["scheme"] = guess[0]  # default to first guess
            else:
                raise InvalidIdentifier(identifier)

    @classmethod
    def _identifiers(cls, alternate_identifiers):
        """Parses identifiers from zenodo alternate identifiers."""
        if not alternate_identifiers:
            return None

        ret = []

        for identifier in alternate_identifiers:
            cls._validate_identifier(identifier)
            _identifier = {
                "scheme": identifier["scheme"],
                "identifier": identifier["identifier"],
            }
            ret.append(_identifier)

        return ret

    @classmethod
    def _related_identifiers(cls, related_identifiers):
        """Parses related identifiers from zenodo."""
        if not related_identifiers:
            return None

        ret = []
        for legacy_identifier in related_identifiers:
            cls._validate_identifier(legacy_identifier)
            rdm_identifier = {
                "scheme": legacy_identifier["scheme"],
                "identifier": legacy_identifier["identifier"],
                "relation_type": {
                    # relation_type is a vocabulary
                    "id": legacy_identifier["relation"].lower(),
                },
            }

            # Resource type is optional.
            legacy_type = legacy_identifier.get("resource_type")
            if legacy_type:
                t = legacy_type["type"]
                st = legacy_type.get("subtype")

                # Map legacy Zenodo resource type to RDM
                # resource_type is a vocabulary
                rdm_type = f"{t}-{st}" if st else t
                rdm_identifier.update({"resource_type": {"id": rdm_type}})

            ret.append(rdm_identifier)

        return ret

    @classmethod
    def _references(cls, references):
        """Parses references from Zenodo."""
        if not references:
            return None

        ret = []

        for reference in references:
            _reference = {
                "reference": reference["raw_reference"],
            }
            ret.append(_reference)

        return ret

    @classmethod
    def _dates(cls, dates):
        """Parses sdates from Zenodo."""
        if not dates:
            return None

        ret = []
        for legacy_date in dates:
            start_date = legacy_date.get("start")
            end_date = legacy_date.get("end")
            description = legacy_date.get("description")

            rdm_date = None
            if start_date and end_date:
                if start_date == end_date:
                    rdm_date = start_date
                else:
                    # TODO what to do
                    rdm_date = f"{start_date}/{end_date}"
            elif start_date:
                rdm_date = start_date

            elif end_date:
                rdm_date = end_date
            # No start_date nor end_date is not allowed on legacy Zenodo

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
            ret.append(rdm_date)

        return ret

    @classmethod
    def _locations(cls, locations):
        """Parses a location from Zenodo."""
        if not locations:
            return None

        features = []
        for legacy_location in locations:
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

    @classmethod
    def _funding(cls, grants):
        """Parses grants from Zenodo to RDM funding."""
        if not grants:
            return None

        ret = []

        for grant in grants:
            if "id" in grant:
                # we skip grants of the format {"id": <grant_id>}
                # TODO: what do we do with the above?
                continue
            # format:    "http://dx.zenodo.org/grants/10.13039/501100000780::278850"
            split = urlparse(grant["$ref"]).path.split("/", 2)
            # returns ['', 'grants', '10.13039/501100000780::278850']
            assert len(split) == 3

            grant_string = split[-1]
            groups = grant_string.split("::", 1)
            assert len(groups) == 2

            funder_doi = groups[0]
            award_id = groups[1]

            funder_doi_or_ror = FUNDER_DOI_TO_ROR.get(funder_doi, funder_doi)

            ret.append(
                {
                    "funder": {"id": funder_doi_or_ror},
                    "award": {"id": f"{funder_doi_or_ror}::{award_id}"},
                }
            )

        return ret

    @classmethod
    def transform(cls, entry):
        """Transform entry."""
        contributors = cls._contributors(entry.get("contributors", []))
        contributors.extend(
            cls._supervisors(entry.get("thesis", {}).get("supervisors", []))
        )

        metadata = {
            "title": entry["title"],
            "description": entry["description"],
            "publication_date": entry["publication_date"],
            "resource_type": cls._resource_type(entry["resource_type"]),
            "creators": cls._creators(entry["creators"]),
            "contributors": contributors,
            "publisher": entry.get("imprint", {}).get("publisher"),
            "additional_descriptions": cls._additional_descriptions(entry.get("notes")),
            "rights": cls._rights(entry.get("license")),
            "languages": cls._languages(entry.get("language")),
            "subjects": cls._subjects(entry.get("keywords")),
            "identifiers": cls._identifiers(entry.get("alternate_identifiers")),
            "related_identifiers": cls._related_identifiers(
                entry.get("related_identifiers")
            ),
            "references": cls._references(entry.get("references")),
            "dates": cls._dates(entry.get("dates")),
            "locations": cls._locations(entry.get("locations")),
            "funding": cls._funding(entry.get("grants")),
        }

        return drop_nones(metadata)


class ZenodoDraftMetadataEntry(ZenodoRecordMetadataEntry):
    """Metadata entry transform."""

    @classmethod
    def transform(cls, entry):
        """Transform entry."""
        contributors = cls._contributors(entry.get("contributors", []))
        contributors.extend(
            cls._supervisors(entry.get("thesis", {}).get("supervisors", []))
        )

        metadata = {
            "title": entry.get("title"),
            "description": entry.get("description"),
            "publication_date": entry.get("publication_date"),
            "contributors": contributors,
            "publisher": entry.get("imprint", {}).get("publisher"),
            "additional_descriptions": cls._additional_descriptions(entry.get("notes")),
            "rights": cls._rights(entry.get("license")),
            "languages": cls._languages(entry.get("language")),
            "subjects": cls._subjects(entry.get("keywords")),
            "identifiers": cls._identifiers(entry.get("alternate_identifiers")),
            "related_identifiers": cls._related_identifiers(
                entry.get("related_identifiers")
            ),
            "references": cls._references(entry.get("references")),
            "dates": cls._dates(entry.get("dates")),
            "locations": cls._locations(entry.get("locations")),
            "funding": cls._funding(entry.get("grants")),
        }

        resource_type = entry.get("resource_type")
        if resource_type:
            metadata["resource_type"] = cls._resource_type(resource_type)

        creators = entry.get("creators")
        if creators:
            metadata["creators"] = cls._creators(creators)

        return drop_nones(metadata)
