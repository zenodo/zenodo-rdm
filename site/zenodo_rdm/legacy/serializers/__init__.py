# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy serializers."""

from flask_resources import BaseListSchema, JSONSerializer, MarshmallowSerializer

from .schemas import LegacySchema


class LegacyJSONSerializer(MarshmallowSerializer):
    """Legacy metadata serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=LegacySchema,
            list_schema_cls=BaseListSchema,
        )
