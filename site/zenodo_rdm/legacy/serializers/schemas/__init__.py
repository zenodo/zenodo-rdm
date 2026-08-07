# SPDX-FileCopyrightText: 2022 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo legacy services."""

from .files import (
    LegacyFileListSchema,
    LegacyFileSchema,
    LegacyFilesRESTListSchema,
    LegacyFilesRESTSchema,
)
from .legacyjson import LegacySchema
from .zenodojson import ZenodoSchema

__all__ = (
    "LegacyFileListSchema",
    "LegacyFileSchema",
    "LegacyFilesRESTListSchema",
    "LegacyFilesRESTSchema",
    "LegacySchema",
    "ZenodoSchema",
)
