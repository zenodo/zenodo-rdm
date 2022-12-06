# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy deserializer schemas."""

from datetime import date

from nameparser import HumanName


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
            r = {"person_or_org": {"type": "personal"}}
            if c.get("affiliation"):
                r["affiliations"] = [{"name": c["affiliation"]}]
            if c.get("orcid"):
                r["person_or_org"]["identifiers"] = [
                    {"scheme": "orcid", "identifier": c["orcid"]},
                ]
            name = HumanName(c["name"])
            r["person_or_org"]["given_name"] = name.first
            r["person_or_org"]["family_name"] = name.surnames

            ret.append(r)
        return ret

    def _metadata(self, data):
        """Transform the metadata of a record."""
        if data:
            return {
                "title": data.get("title"),
                "description": data.get("description"),
                "publication_date": data.get(
                    "publication_date",
                    date.today().isoformat(),
                ),
                "resource_type": self._resource_type(data),
                "creators": self._creators(data.get("creators")),
                # NOTE: Hardcoded for DataCite
                "publisher": "Zenodo",
            }

    def load(self, data):
        """Transform data."""
        return {
            "metadata": self._metadata(data.get("metadata")),
            # TODO: Map old access rights to RDM access
            # "access": self._access(data.get('access')),
            "files": {"enabled": True},
        }
