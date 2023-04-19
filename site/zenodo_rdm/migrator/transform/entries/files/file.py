# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator files instance entry transformer."""

from invenio_rdm_migrator.streams.files.transform import FilesInstanceEntry

from .mixin import ZenodoFilesEntryMixin


class ZenodoFilesInstanceEntry(FilesInstanceEntry, ZenodoFilesEntryMixin):
    """Transform a single file instance entry."""

    ns_key = "ff_"

    def _id(self, entry):
        """Returns the file instance ID."""
        return self.get_field(entry, "id")

    def _created(self, entry):
        """Returns the creation date."""
        return self.get_field(entry, "created")

    def _updated(self, entry):
        """Returns the update date."""
        return self.get_field(entry, "updated")

    def _uri(self, entry):
        """Returns the file uri."""
        # TODO: point to an existing file to test
        return self.get_field(entry, "uri")

    def _storage_class(self, entry):
        """Returns the file instance storage class."""
        storage_class = self.get_field(entry, "storage_class")
        return "L" if storage_class == "S" else storage_class

    def _size(self, entry):
        """Returns the file instance size."""
        return self.get_field(entry, "size")

    def _checksum(self, entry):
        """Returns the file instance checksum."""
        return self.get_field(entry, "checksum")

    def _readable(self, entry):
        """Returns if the file instance can be read."""
        return self.get_field(entry, "readable")

    def _writable(self, entry):
        """Returns if the file instance can be written."""
        return self.get_field(entry, "writable")

    def _last_check_at(self, entry):
        """Returns the last date the file was checked."""
        return self.get_field(entry, "last_check_at")

    def _last_check(self, entry):
        """Returns if the file instance was last checked."""
        return self.get_field(entry, "last_check")
