# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator records transformers."""

from invenio_rdm_migrator.streams.records import RDMRecordEntry, RDMRecordTransform
from nameparser import HumanName


class ZenodoRecordEntry(RDMRecordEntry):
    """Transform Zenodo record to RDM record."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return entry["version_id"]

    def _index(self, entry):
        """Returns the index of the record."""
        return entry.get("index", 0) + 1  # in legacy we start at 0

    def _recid(self, entry):
        """Returns the recid of the record."""
        return str(entry["json"]["recid"])

    def _pids(self, entry):
        record = entry["json"]
        r = {
            "oai": {
                "provider": "oai",
                "identifier": record["_oai"]["id"],
            },
        }
        if record.get("doi"):
            r["doi"] = {
                "client": "datacite",
                "provider": "datacite",
                "identifier": record["doi"],
            }

        return r

    def _files(self, entry):
        """Transform the files of a record."""
        return {"enabled": True}

    def _access(self, entry):
        record = entry["json"]
        is_open = record["access_right"] == "open"
        r = {
            "record": "public",
            "files": "public" if is_open else "restricted",
        }
        if record["access_right"] == "embargoed":
            r["embargo"] = {
                "until": record["embargo_date"],
                "active": True,
            }
        return r

    def _metadata(self, entry):
        """Transform the metadata of a record."""

        def _person_or_org(creatibutor):
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

        def _creators(data):
            ret = []
            for c in data:
                r = {"person_or_org": _person_or_org(c)}
                if c.get("affiliation"):
                    r["affiliations"] = [{"name": c["affiliation"]}]
                ret.append(r)

            return ret

        def _resource_type(data):
            t = data["type"]
            st = data.get("subtype")
            return {"id": f"{t}-{st}"} if st else {"id": t}

        def _contributors(data):
            return []

        def _supervisors(data):
            ret = []
            for c in data:
                r = {"person_or_org": _person_or_org(c)}
                if c.get("affiliation"):
                    r["affiliations"] = [{"name": c["affiliation"]}]
                r["role"] = {"id": "supervisor"}
                ret.append(r)

            return ret

        record = entry["json"]
        contributors = _contributors(record.get("contributors", []))
        contributors.extend(
            _supervisors(record.get("thesis", {}).get("supervisors", []))
        )

        r = {
            "title": record["title"],
            "description": record["description"],
            "publication_date": record["publication_date"],
            "resource_type": _resource_type(record["resource_type"]),
            "creators": _creators(record["creators"]),
            "contributors": contributors,
            "publisher": record.get("imprint", {}).get("publisher"),
        }

        return r

    def _custom_fields(self, entry):
        """Transform custom fields."""
        metadata = entry.get("json", {})
        cf = {
            "journal:journal": {
                "title": metadata.get("journal", {}).get("title"),
                "issue": metadata.get("journal", {}).get("issue"),
                "pages": metadata.get("journal", {}).get("pages"),
                "volume": metadata.get("journal", {}).get("volume"),
                "issn": metadata.get("journal", {}).get("issn"),
            },
            "meeting:meeting": {
                "acronym": metadata.get("meeting", {}).get("acronym"),
                "dates": metadata.get("meeting", {}).get("dates"),
                "place": metadata.get("meeting", {}).get("place"),
                "session_part": metadata.get("meeting", {}).get("session_part"),
                "session": metadata.get("meeting", {}).get("session"),
                "title": metadata.get("meeting", {}).get("title"),
                "url": metadata.get("meeting", {}).get("url"),
            },
            "imprint:imprint": {
                "isbn": metadata.get("imprint", {}).get("isbn"),
                "place": metadata.get("imprint", {}).get("place"),
                "title": metadata.get("part_of", {}).get("title"),
                "pages": metadata.get("part_of", {}).get("pages"),
            },
            "thesis:university": metadata.get("thesis", {}).get("university"),
        }

        return self._drop_nones(cf)

    def _drop_nones(self, d):
        """Recursively drop Nones in dict d and return a new dictionary."""
        dd = {}
        for k, v in d.items():
            if isinstance(v, dict) and v:  # second clause removes empty dicts
                dd[k] = self._drop_nones(v)
            elif v is not None:
                dd[k] = v
        return dd


class ZenodoRecordTransform(RDMRecordTransform):
    """Zenodo to RDM Record class for data transformation."""

    def _community_id(self, entry):
        communities = entry["json"].get("communities")
        if communities:
            # TODO: handle all slugs
            slug = communities[0]
            if slug:
                return {"ids": [slug], "default": slug}
        return {}

    def _parent(self, entry):
        parent = {
            "created": entry["created"],  # same as the record
            "updated": entry["updated"],  # same as the record
            "version_id": entry["version_id"],
            "json": {
                # loader is responsible for creating/updating if the PID exists.
                "id": entry["json"]["conceptrecid"],
                "access": {
                    "owned_by": [{"user": o} for o in entry["json"].get("owners", [])]
                },
                "communities": self._community_id(entry),
            },
        }

        return parent

    def _record(self, entry):
        return ZenodoRecordEntry().transform(entry)

    def _draft(self, entry):
        return None

    def _draft_files(self, entry):
        return None

    def _record_files(self, entry):
        files = entry["json"].get("_files", [])
        return [
            {
                "key": f["key"],
                "object_version": {
                    "file": {
                        "size": f["size"],
                        "checksum": f["checksum"],
                    },
                },
            }
            for f in files
        ]
