# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy serializers."""

from flask_resources import BaseListSchema, JSONSerializer, MarshmallowSerializer
from marshmallow import fields, missing, post_dump

from .schemas import (
    LegacyFileListSchema,
    LegacyFileSchema,
    LegacyFilesRESTSchema,
    LegacySchema,
    ZenodoSchema,
)


class LegacyListSchema(BaseListSchema):
    """Legacy top-level array/list schema."""

    class Meta:
        """Meta class."""

        exclude = ("aggregations",)

    @post_dump()
    def unwrap_hits(self, data, many, **kwargs):
        """Unwrap hits into a top-level array result."""
        return data.get("hits", {}).get("hits", [])


class ZenodoListSchema(BaseListSchema):
    """Zenodo top-level List schema."""

    sortBy = fields.Field(load_only=True)


class LegacyJSONSerializer(MarshmallowSerializer):
    """Legacy metadata serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=LegacySchema,
            list_schema_cls=LegacyListSchema,
        )


class ZenodoJSONSerializer(MarshmallowSerializer):
    """Legacy metadata serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ZenodoSchema,
            list_schema_cls=ZenodoListSchema,
        )


class LegacyDraftFileJSONSerializer(MarshmallowSerializer):
    """Legacy draft file serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=LegacyFileSchema,
            list_schema_cls=LegacyFileListSchema,
        )


class LegacyFilesRESTJSONSerializer(MarshmallowSerializer):
    """Legacy Files-REST serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=LegacyFilesRESTSchema,
            list_schema_cls=BaseListSchema,
        )
