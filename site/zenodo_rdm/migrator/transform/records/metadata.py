# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator metadata entry transformer."""

from invenio_rdm_migrator.transform import Entry
from nameparser import HumanName


class ZenodoMetadataEntry(Entry):
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
        }

        return metadata
