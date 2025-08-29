# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo resources config."""

import copy

from flask_resources import ResponseHandler
from invenio_rdm_records.resources.config import (
    record_serializers as default_record_serializers,
)
from invenio_records_resources.resources.records.headers import etag_headers

from . import serializers
from .legacy.serializers import ZenodoJSONSerializer

record_serializers = copy.deepcopy(default_record_serializers)
record_serializers.update(
    {
        "application/json": ResponseHandler(
            ZenodoJSONSerializer(), headers=etag_headers
        ),
        "application/vnd.zenodo.v1+json": ResponseHandler(
            ZenodoJSONSerializer(), headers=etag_headers
        ),
        "application/vnd.datacite.datacite+xml": ResponseHandler(
            serializers.ZenodoDataciteXMLSerializer(), headers=etag_headers
        ),
        "application/vnd.datacite.datacite+json": ResponseHandler(
            serializers.ZenodoDataciteJSONSerializer(), headers=etag_headers
        ),
        "application/x-bibtex": ResponseHandler(
            serializers.ZenodoBibtexSerializer(), headers=etag_headers
        ),
    }
)

# Alias for the DataCite XML serializer
record_serializers["application/x-datacite+xml"] = record_serializers[
    "application/vnd.datacite.datacite+xml"
]
