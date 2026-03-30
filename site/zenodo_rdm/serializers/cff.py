# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo CFF serializer."""

import yaml
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import SimpleSerializer
from invenio_rdm_records.resources.serializers.cff.schema import CFFSchema
from marshmallow import missing


class ZenodoCFFSchema(CFFSchema):
    """Zenodo Codemeta schema."""

    def get_identifiers(self, obj):
        """Get identifiers."""
        ret = super().get_identifiers(obj) or []
        swhid = obj.get("swh", {}).get("swhid")
        if swhid:
            ret.append({"value": swhid, "type": "swh"})
        return ret or missing


class ZenodoCFFSerializer(MarshmallowSerializer):
    """Zenodo Codemeta serializer."""

    def __init__(self, **options):
        """Initialize serializer."""
        encoder = options.get("encoder", yaml.dump)
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=ZenodoCFFSchema,
            list_schema_cls=BaseListSchema,
            encoder=encoder,
            **options,
        )
