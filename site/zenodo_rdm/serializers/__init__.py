# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo serializers."""

from .bibtex import ZenodoBibtexSerializer
from .cff import ZenodoCFFSerializer
from .codemeta import ZenodoCodemetaSerializer
from .datacite import ZenodoDataciteJSONSerializer, ZenodoDataciteXMLSerializer

__all__ = (
    "ZenodoBibtexSerializer",
    "ZenodoCodemetaSerializer",
    "ZenodoDataciteJSONSerializer",
    "ZenodoDataciteXMLSerializer",
    "ZenodoCFFSerializer",
)
