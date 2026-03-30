# SPDX-FileCopyrightText: 2022 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo legacy deserializers."""

from flask_resources import JSONDeserializer

from .schemas import LegacySchema


class LegacyJSONDeserializer(JSONDeserializer):
    """Legacy metadata deserializer."""

    def deserialize(self, data):
        """Deserialize the payload."""
        data = super().deserialize(data)
        return LegacySchema().load(data)
