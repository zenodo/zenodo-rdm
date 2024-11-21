# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo bibtex serializer."""

from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer
from invenio_rdm_records.contrib.codemeta.processors import CodemetaDumper
from invenio_rdm_records.resources.serializers.codemeta.schema import CodemetaSchema
from invenio_rdm_records.resources.serializers.schemaorg.schema import (
    _serialize_identifiers,
)
from marshmallow import fields, missing


class ZenodoCodemetaSchema(CodemetaSchema):
    """Zenodo Codemeta schema."""

    def get_sameAs(self, obj):
        """Get sameAs field."""
        ret = super().get_sameAs(obj) or []
        swhid = obj.get("swh", {}).get("swhid")
        if swhid:
            ret.append({"@id": swhid})
        return ret or missing


class ZenodoCodemetaSerializer(MarshmallowSerializer):
    """Zenodo Codemeta serializer."""

    def __init__(self, **options):
        """Initialize serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ZenodoCodemetaSchema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [CodemetaDumper()]},  # Order matters
            **options
        )
