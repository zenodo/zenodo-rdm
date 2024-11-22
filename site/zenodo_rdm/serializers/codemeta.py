# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo codemeta serializer."""

from flask import current_app
from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer
from idutils import normalize_doi, to_url
from invenio_rdm_records.contrib.codemeta.processors import CodemetaDumper
from invenio_rdm_records.resources.serializers.codemeta.schema import CodemetaSchema
from marshmallow import fields, missing


class ZenodoCodemetaSchema(CodemetaSchema):
    """Zenodo Codemeta schema."""

    identifier = fields.Method("get_identifiers")

    def get_identifiers(self, obj):
        """Compute the "identifier".

        It uses the DOI expressed as a URL and the Software Hash ID as `swhid`.
        If only one identifier is present, it returns it as a single entry.
        """
        doi = obj.get("pids", {}).get("doi", {}).get("identifier")
        ret = []
        if doi:
            doi_url = to_url(normalize_doi(doi), "doi")
            ret.append({"@type": "doi", "value": doi, "propertyID": doi_url})
        swhid = obj.get("swh", {}).get("swhid")
        if swhid:
            swh_url = f"{current_app.config['SWH_UI_BASE_URL']}/{swhid}"
            ret.append({"@type": "swhid", "value": swhid, "propertyID": swh_url})
        if len(ret) == 1:
            return ret[0]
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
            **options,
        )
