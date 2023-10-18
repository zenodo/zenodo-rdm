# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Github specific schemas."""

from flask import current_app
from idutils import is_orcid
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates,
)
from marshmallow_utils.fields import SanitizedHTML, SanitizedUnicode
from werkzeug.local import LocalProxy

invenio_records_ext = LocalProxy(lambda: current_app.extensions["invenio-records"])


class AuthorSchema(Schema):
    """Schema for a person."""

    class Meta:
        """Exclude unknown fields."""

        unknown = EXCLUDE

    name = SanitizedUnicode()
    affiliation = SanitizedUnicode()
    orcid = fields.String()

    @validates("orcid")
    def validate_orcid(self, value):
        """Validate orcid."""
        if value != "" and not is_orcid(value):
            raise ValidationError(f"Invalid orcid provided : {value}")

    @post_load(pass_original=True)
    def load_name(self, in_data, original, **kwargs):
        """Load name field on post load.

        ..note ::

            Why post load - marshmallow does not allow the usage of fields.Method(deserialize="xyz") if the attribute key is not in the input data.
        """
        family_name = original.get("family-names")
        given_name = original.get("given-names")
        org_name = original.get("name")
        if org_name:
            name = org_name
        elif family_name and given_name:
            name = f"{family_name}, {given_name}"
        else:
            name = family_name or given_name
        in_data["name"] = name
        return in_data


class CitationMetadataSchema(Schema):
    """Minimal CITATION.cff metadata schema.

    This schema was migrated as-is from legacy Zenodo.

    .. note::

      There is a more complete CFF schema being developed which will obsolete this one.
    """

    class Meta:
        """Exclude unknown fields."""

        unknown = EXCLUDE

    description = SanitizedHTML(data_key="abstract")
    creators = fields.List(fields.Nested(AuthorSchema), data_key="authors")
    keywords = fields.List(SanitizedUnicode())
    license = SanitizedUnicode()
    title = SanitizedUnicode(required=True, validate=validate.Length(min=3))
    notes = SanitizedHTML(data_key="message")

    # TODO: Add later
    # alternate_identifiers = fields.Raw(load_from='identifiers')
    # related_identifiers = fields.Raw(load_from='references')

    subschema = {
        "audiovisual": "video",
        "art": "other",
        "bill": "other",
        "blog": "other",
        "catalogue": "other",
        "conference-paper": "conference",
        "database": "data",
        "dictionary": "other",
        "edited-work": "other",
        "encyclopedia": "other",
        "film-broadcast": "video",
        "government-document": "other",
        "grant": "other",
        "hearing": "other",
        "historical-work": "other",
        "legal-case": "other",
        "legal-rule": "other",
        "magazine-article": "other",
        "manual": "other",
        "map": "other",
        "multimedia": "video",
        "music": "other",
        "newspaper-article": "other",
        "pamphlet": "other",
        "patent": "other",
        "personal-communication": "other",
        "proceedings": "other",
        "report": "other",
        "serial": "other",
        "slides": "other",
        "software-code": "software",
        "software-container": "software",
        "software-executable": "software",
        "software-virtual-machine": "software",
        "sound-recording": "other",
        "standard": "other",
        "statute": "other",
        "website": "other",
    }
