# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy serializers."""

from flask_resources import (BaseListSchema, JSONSerializer,
                             MarshmallowSerializer)
from invenio_rdm_records.resources.serializers.marcxml import \
    MARCXMLSerializer as BaseMARCXMLSerializer
from marshmallow import fields, missing, post_dump

from .schemas import (LegacyFileListSchema, LegacyFileSchema,
                      LegacyFilesRESTSchema, LegacySchema, MARCXMLSchema,
                      ZenodoSchema)


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


class MARCXMLSerializer(BaseMARCXMLSerializer):
    """Marshmallow based MARCXML serializer for records."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(object_schema_cls=MARCXMLSchema)
