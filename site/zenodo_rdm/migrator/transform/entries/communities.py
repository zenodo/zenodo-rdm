# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo migrator communities transformer entries."""

from invenio_rdm_migrator.streams.communities import (
    CommunityEntry,
    CommunityMemberEntry,
    FeaturedCommunityEntry,
)


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


class ZenodoCommunityEntry(CommunityEntry):
    """Transform Zenodo community to RDM community."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return 1

    def _files(self, entry):
        """Transform the files of a record."""
        return {"enabled": True}

    def _slug(self, entry):
        """Returns the community slug."""
        return entry["id"]

    def _access(self, entry):
        """Returns community access."""
        return {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        }

    def _bucket_id(self, entry):
        """Returns the community bucket id."""
        return None

    def _metadata(self, entry):
        """Returns community metadata."""
        return {
            "page": entry["page"],
            "title": entry["title"],
            "curation_policy": entry["curation_policy"],
            "description": entry["description"],
        }


class ZenodoCommunityMemberEntry(CommunityMemberEntry):
    """Transform Zenodo community members to RDM community members."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return 1

    def _role(self, entry):
        """Returns the community member role."""
        return "owner"

    def _visible(self, entry):
        """Returns if the community member is visible or not."""
        return True

    def _active(self, entry):
        """Returns if the community member is active or not."""
        return True

    def _user_id(self, entry):
        """Returns the community member user id, if the member is a single user."""
        return entry["id_user"]

    def _group_id(self, entry):
        """Returns the community member group id, if the member is a group."""
        return None

    def _request_id(self, entry):
        """Returns the community member request id, if there is any request associated with the community member."""
        return None
