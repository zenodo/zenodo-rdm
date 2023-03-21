# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator custom fields entry transformer."""

from invenio_rdm_migrator.transform import Entry


class ZenodoCustomFieldsEntry(Entry):
    """Custom fields entry transform."""

    @classmethod
    def _journal(cls, journal):
        """Parse journal fields."""
        return {
            "title": journal.get("title"),
            "issue": journal.get("issue"),
            "pages": journal.get("pages"),
            "volume": journal.get("volume"),
            "issn": journal.get("issn"),
        }

    @classmethod
    def _meeting(cls, meeting):
        """Parse meeting fields."""
        return {
            "acronym": meeting.get("acronym"),
            "dates": meeting.get("dates"),
            "place": meeting.get("place"),
            "session_part": meeting.get("session_part"),
            "session": meeting.get("session"),
            "title": meeting.get("title"),
            "url": meeting.get("url"),
        }

    @classmethod
    def _imprint(cls, imprint, part_of):
        """Parse imprint fields."""
        return {
            "isbn": imprint.get("isbn"),
            "place": imprint.get("place"),
            "title": part_of.get("title"),
            "pages": part_of.get("pages"),
        }

    @classmethod
    def _drop_nones(cls, d):
        """Recursively drop Nones in dict d and return a new dictionary."""
        dd = {}
        for k, v in d.items():
            if isinstance(v, dict) and v:  # second clause removes empty dicts
                dd[k] = cls._drop_nones(v)
            elif v is not None:
                dd[k] = v
        return dd

    @classmethod
    def transform(cls, entry):
        """Transform entry."""
        custom_fields = {
            "journal:journal": cls._journal(entry.get("journal", {})),
            "meeting:meeting": cls._meeting(entry.get("meeting", {})),
            "imprint:imprint": cls._imprint(
                entry.get("imprint", {}), entry.get("part_of", {})
            ),
            "thesis:university": entry.get("thesis", {}).get("university"),
        }

        return cls._drop_nones(custom_fields)
