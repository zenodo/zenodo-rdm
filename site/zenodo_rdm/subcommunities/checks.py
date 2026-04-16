# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo-specific subcommunity checks."""

from invenio_checks.contrib.metadata.check import MetadataCheck


class SubcommunityMetadataCheck(MetadataCheck):
    """Check for validating community metadata against configured rules."""

    id = "subcommunity_metadata"
    title = "Community metadata"
    description = "The following metadata was automatically suggested based on the selected EU project."
    sort_order = 34

