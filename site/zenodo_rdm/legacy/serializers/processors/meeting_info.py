# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Journal serialization processing."""

from flask_resources.serializers import DumperMixin


class MeetingInfoMarcXMLDumper(DumperMixin):
    """Dumper for MarcXML serialization of 'Journal' custom field."""

    def post_dump(self, data, original=None, **kwargs):
        """Adds serialized journal data to the input data under the '773' key."""
        _original = original or {}
        custom_fields = _original.get("custom_fields", {})
        journal_data = custom_fields.get("journal:journal", {})

        if not journal_data:
            return data

        items_dict = {}
        field_keys = {
            "p": journal_data.get("title"),
            "v": journal_data.get("volume"),
            "n": journal_data.get("issue"),
            "c": journal_data.get("pages"),
            "y": _original.get("metadata", {}).get("publication_date"),
        }
        for key, value in field_keys.items():
            if value:
                items_dict[key] = value

        if not items_dict:
            return data

        code = "909C4"
        existing_data = data.get(code)
        if existing_data and isinstance(existing_data, list):
            data[code].append(items_dict)
        else:
            data[code] = [items_dict]
        return data
