# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy services."""

from .files import LegacyFileSchema, LegacyFilesRESTSchema
from .legacyjson import LegacySchema
from .zenodojson import ZenodoSchema

__all__ = (
    "LegacySchema",
    "LegacyFileSchema",
    "LegacyFilesRESTSchema",
    "ZenodoSchema",
)
