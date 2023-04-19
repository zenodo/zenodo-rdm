# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator files bucket entry transformer."""

from invenio_rdm_migrator.streams.files.transform import FilesBucketEntry

from .mixin import ZenodoFilesEntryMixin


class ZenodoFilesBucketEntry(FilesBucketEntry, ZenodoFilesEntryMixin):
    """Zenodo transform a single file bucket entry."""

    ns_key = "fb_"

    def _id(self, entry):
        """Returns the file bucket ID."""
        return self.get_field(entry, "id")

    def _created(self, entry):
        """Returns the creation date."""
        return self.get_field(entry, "created")

    def _updated(self, entry):
        """Returns the update date."""
        return self.get_field(entry, "updated")

    def _default_location(self, entry):
        """Returns the file bucket default location."""
        return self.get_field(entry, "default_location")

    def _default_storage_class(self, entry):
        """Returns the file bucket default storage class."""
        storage_class = self.get_field(entry, "default_storage_class")
        return "L" if storage_class == "S" else storage_class

    def _size(self, entry):
        """Returns the file bucket size."""
        return self.get_field(entry, "size")

    def _quota_size(self, entry):
        """Returns the file bucket quota size."""
        return self.get_field(entry, "quota_size")

    def _max_file_size(self, entry):
        """Returns the file bucket max file size."""
        return self.get_field(entry, "max_file_size")

    def _locked(self, entry):
        """Returns if the file bucket is locked."""
        return self.get_field(entry, "locked")

    def _deleted(self, entry):
        """Returns if the file bucket is deleted."""
        return self.get_field(entry, "deleted")
