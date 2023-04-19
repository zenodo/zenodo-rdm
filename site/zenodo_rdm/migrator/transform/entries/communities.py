# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo migrator communities transformer entries."""

from invenio_rdm_migrator.streams.communities import FeaturedCommunityEntry


class ZenodoFeaturedCommunityEntry(FeaturedCommunityEntry):
    """Transform Zenodo featured community to RDM community."""

    def _created(self, entry):
        """Returns the creation date."""
        return entry["featured_created"]

    def _updated(self, entry):
        """Returns the update date."""
        return entry["featured_updated"]

    def _start_date(self, entry):
        """Returns the start date."""
        return entry["featured_start_date"]
