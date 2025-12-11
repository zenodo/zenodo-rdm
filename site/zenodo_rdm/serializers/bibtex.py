# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo bibtex serializer."""

from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer
from invenio_rdm_records.resources.serializers.bibtex.schema import BibTexSchema
from marshmallow import fields, missing


class ZenodoBibtexSchema(BibTexSchema):
    """Zenodo bibtex schema."""

    swhid = fields.Method("get_swhid")

    def get_swhid(self, obj):
        """Get swhid."""
        return obj.get("swh", {}).get("swhid") or missing


class ZenodoBibtexSerializer(MarshmallowSerializer):
    """Zenodo bibtex serializer."""

    def __init__(self, **options):
        """Initialize serializer."""
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=ZenodoBibtexSchema,
            list_schema_cls=BaseListSchema,
            encoder=self.bibtex_tostring,
        )

    @classmethod
    def bibtex_tostring(cls, record):
        """Stringify a BibTex record."""
        return record
