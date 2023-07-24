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
    ZenodoCommunityFileEntry,
    ZenodoCommunityFilesBucketEntry,
    ZenodoCommunityFilesObjectVersionEntry,
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
        if entry.get("is_featured", False):
            return ZenodoFeaturedCommunityEntry().transform(entry)
        return {}

    def _community_files(self, entry):
        """Transform the community files."""
        logo_file_id = entry.get("logo_file_id")
        file_entry = (
            ZenodoCommunityFileEntry().transform(entry) if logo_file_id else None
        )
        return {
            "file": file_entry,
            "bucket": ZenodoCommunityFilesBucketEntry().transform(entry),
            "file_object": ZenodoCommunityFilesObjectVersionEntry().transform(entry),
        }
