# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy services."""

from .files import (LegacyFileListSchema, LegacyFileSchema,
                    LegacyFilesRESTSchema)
from .legacyjson import LegacySchema
from .marcxml import MARCXMLSchema
from .zenodojson import ZenodoSchema

__all__ = (
    "LegacyFileListSchema",
    "LegacyFileSchema",
    "LegacyFilesRESTSchema",
    "LegacySchema",
    "ZenodoSchema",
    "MARCXMLSchema",
)
