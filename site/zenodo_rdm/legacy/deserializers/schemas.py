# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy deserializer schemas."""

from datetime import date

from invenio_records.dictutils import clear_none
from nameparser import HumanName

from ..vocabularies.licenses import LEGACY_LICENSES, legacy_to_rdm

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

        rdm_additional_descriptions = [{"description": data, "type": {"id": "other"}}]

        return rdm_additional_descriptions

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
                "rights": self._rights(data.get("license")),
                "contributors": self._contributors(data),
                "additional_descriptions": self._additional_descriptions(
                    data.get("notes")
                ),
            }

    def load(self, data):
        """Transform data."""
        if not data:
            return {}

        return {
            "metadata": self._metadata(data.get("metadata")),
            "custom_fields": self._custom_fields(data.get("metadata")),
            # TODO: Map old access rights to RDM access
            # "access": self._access(data.get('access')),
            "files": {"enabled": True},
        }
