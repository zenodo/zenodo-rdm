# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator communities transformers."""

from invenio_rdm_migrator.streams.communities import CommunityTransform

from .entries.communities import (
    ZenodoCommunityEntry,
    ZenodoCommunityMemberEntry,
    ZenodoFeaturedCommunityEntry,
)


class ZenodoCommunityTransform(CommunityTransform):
    """Zenodo to RDM Community class for data transformation."""

    def _community(self, entry):
        return ZenodoCommunityEntry().transform(entry)

    def _community_members(self, entry):
        """Transform the community members."""
        return [ZenodoCommunityMemberEntry().transform(entry)]

    def _featured_community(self, entry):
        """Transform the featured community."""
        if entry["is_featured"]:
            return ZenodoFeaturedCommunityEntry().transform(entry)
        return {}
