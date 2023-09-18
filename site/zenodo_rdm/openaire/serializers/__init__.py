# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE serializers."""

from flask_resources import BaseListSchema, JSONSerializer
from flask_resources.serializers import MarshmallowSerializer

from .schema import OpenAIRESchema


class OpenAIREV1Serializer(MarshmallowSerializer):
    """Marshmallow based DataCite serializer for records."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=OpenAIRESchema,
            list_schema_cls=BaseListSchema,
            **options
        )
