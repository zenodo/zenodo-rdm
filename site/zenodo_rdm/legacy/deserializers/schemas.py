# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy deserializer schemas."""

from datetime import date

from nameparser import HumanName

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
                "creators": self._creators(data.get("creators", [])),
                # NOTE: Hardcoded for DataCite
                "publisher": "Zenodo",
                "funding": self._funding(data.get("grants", [])),
            }

    def load(self, data):
        """Transform data."""
        return {
            "metadata": self._metadata(data.get("metadata")),
            # TODO: Map old access rights to RDM access
            # "access": self._access(data.get('access')),
            "files": {"enabled": True},
        }
