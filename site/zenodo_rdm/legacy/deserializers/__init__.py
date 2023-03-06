# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy deserializers."""

from flask_resources import JSONDeserializer

from .schemas import LegacyRecordTransform


class LegacyJSONDeserializer(JSONDeserializer):
    """Legacy metadata deserializer."""

    def deserialize(self, data):
        """Deserialize the payload."""
        data = super().deserialize(data)
        return LegacyRecordTransform().load(data)
