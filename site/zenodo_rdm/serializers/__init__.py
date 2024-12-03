# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo serializers."""

from .bibtex import ZenodoBibtexSerializer
from .cff import ZenodoCFFSerializer
from .codemeta import ZenodoCodemetaSerializer
from .datacite import ZenodoDataciteJSONSerializer, ZenodoDataciteXMLSerializer
from .dcat import ZenodoDCATSerializer

__all__ = (
    "ZenodoBibtexSerializer",
    "ZenodoCodemetaSerializer",
    "ZenodoDataciteJSONSerializer",
    "ZenodoDataciteXMLSerializer",
    "ZenodoCFFSerializer",
    "ZenodoDCATSerializer",
)
