# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo datacite serializer."""

from datacite import schema43
from flask import current_app
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer, SimpleSerializer
from invenio_rdm_records.contrib.journal.processors import JournalDataciteDumper
from invenio_rdm_records.resources.serializers.datacite.schema import DataCite45Schema
from marshmallow import missing


class ZenodoDataciteSchema(DataCite45Schema):
    """Zenodo Datacite schema."""

    def get_related_identifiers(self, obj):
        """Get related identifiers."""
        ret = super().get_related_identifiers(obj) or []
        swhid = obj.get("swh", {}).get("swhid")
        if swhid:
            _url = f"{current_app.config['SWH_UI_BASE_URL']}/{swhid}"
            ret.append(
                {
                    "relatedIdentifier": _url,
                    "relatedIdentifierType": "URL",
                    "relationType": "IsIdenticalTo",
                }
            )
        return ret or missing


class ZenodoDataciteJSONSerializer(MarshmallowSerializer):
    """Zenodo Datacite serializer."""

    def __init__(self, **options):
        """Instantiate serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ZenodoDataciteSchema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalDataciteDumper()]},  # Order matters
            **options,
        )


class ZenodoDataciteXMLSerializer(MarshmallowSerializer):
    """Zenodo Datacite XML serializer."""

    def __init__(self, **options):
        """Instantiate serializer."""
        encoder = options.get("encoder", schema43.tostring)
        super().__init__(
            format_serializer_cls=SimpleSerializer,
            object_schema_cls=ZenodoDataciteSchema,
            list_schema_cls=BaseListSchema,
            schema_kwargs={"dumpers": [JournalDataciteDumper()]},  # Order matters
            encoder=encoder,
        )
