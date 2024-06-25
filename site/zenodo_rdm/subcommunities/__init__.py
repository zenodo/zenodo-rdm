# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Subcommunities implementation."""

from .request import ZenodoSubCommunityRequest
from .schema import ZenodoSubcommunityRequestSchema

__all__ = (
    "ZenodoSubcommunityRequestSchema",
    "ZenodoSubCommunityRequest",
)
