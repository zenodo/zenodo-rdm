# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""

from invenio_records_resources.services.custom_fields import BaseCF, KeywordCF
from marshmallow import fields
from marshmallow_utils.fields import SanitizedUnicode


class SubjectListCF(BaseCF):
    """Subject list custom field."""

    @property
    def mapping(self):
        """Search mapping."""
        return {
            "type": "object",
            "properties": {
                "term": {"type": "keyword"},
                "identifier": {"type": "keyword"},
                "scheme": {"type": "keyword"},
            },
        }

    @property
    def field(self):
        """Marshmallow field."""
        return fields.List(
            fields.Nested(
                {
                    "term": SanitizedUnicode(),
                    "identifier": SanitizedUnicode(),
                    "scheme": SanitizedUnicode(),
                }
            )
        )


LEGACY_CUSTOM_FIELDS = [
    KeywordCF(name="legacy:communities", multiple=True),
    SubjectListCF(name="legacy:subjects"),
]
"""Legacy compatibility custom fields."""
