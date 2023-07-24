# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo migrator communities transformer entries."""

from invenio_rdm_migrator.streams.communities import (
    CommunityEntry,
    CommunityFileEntry,
    CommunityMemberEntry,
    FeaturedCommunityEntry,
)
from invenio_rdm_migrator.streams.files import FilesBucketEntry, FilesObjectVersionEntry


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


class ZenodoCommunityFileEntry(CommunityFileEntry):
    """Transform Zenodo community file."""

    def _created(self, entry):
        """Returns the creation date."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the update date."""
        return entry["updated"]

    def _json(self, entry):
        """Returns an empty object as the file's metadata."""
        return {}

    def _version_id(self, entry):
        """Returns the file version id, hardcoded to one."""
        return 1

    def _key(self, entry):
        """The filepath must be 'logo' for the community logo."""
        return "logo"

    def _id(self, entry):
        """Returns the file id."""
        return entry["logo_file_id"]


class ZenodoCommunityFilesBucketEntry(FilesBucketEntry):
    """Transform zenodo community logo to rdm file."""

    def _id(self, entry):
        """The file bucket id is empty for now and auto generated after."""
        pass

    def _created(self, entry):
        """Returns the creation date."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the update date."""
        return entry["updated"]

    def _default_location(self, entry):
        """Returns the file bucket default location, hardcoded to one."""
        return 1

    def _default_storage_class(self, entry):
        """Returns the file bucket default storage class, hardcoded to 'L' ('local')."""
        return "L"

    def _size(self, entry):
        """Returns the file bucket size, since the logo is not yet updated it returns 0."""
        return 0  # TODO should be the logo size?

    def _quota_size(self, entry):
        """The file bucket quota size is nullable."""
        return None

    def _max_file_size(self, entry):
        """The file bucket max file size is nullable."""
        return None

    def _locked(self, entry):
        """The file bucket is not locked."""
        return False

    def _deleted(self, entry):
        """The file bucket is not deleted."""
        return False


class ZenodoCommunityFilesObjectVersionEntry(FilesObjectVersionEntry):
    """Transform zenodo file object to RDM."""

    def _created(self, entry):
        """Returns the creation date."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the update date."""
        return entry["updated"]

    def _key(self, entry):
        """The file key name must be 'logo' for the community logo."""
        return "logo"

    def _mimetype(self, entry):
        """Mimetype is nullable."""
        return None

    def _is_head(self, entry):
        """Community file logo will be the head."""
        return True

    def _version_id(self, entry):
        """Version id will be later auto generated."""
        return None

    def _bucket_id(self, entry):
        """The bucket id is added afterwards."""
        return None

    def _file_id(self, entry):
        """The file id is added afterwards."""
        return None
