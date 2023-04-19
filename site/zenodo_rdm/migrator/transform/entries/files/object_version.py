# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator files object version entry transformer."""

from invenio_rdm_migrator.streams.files.transform import FilesObjectVersionEntry

from .mixin import ZenodoFilesEntryMixin


class ZenodoFilesObjectVersionEntry(FilesObjectVersionEntry, ZenodoFilesEntryMixin):
    """Transform a single file object version entry."""

    ns_key = "fo_"

    def _version_id(self, entry):
        """Returns the file object version ID."""
        return self.get_field(entry, "version_id")

    def _created(self, entry):
        """Returns the creation date."""
        return self.get_field(entry, "created")

    def _updated(self, entry):
        """Returns the update date."""
        return self.get_field(entry, "updated")

    def _key(self, entry):
        """Returns the file key name."""
        return self.get_field(entry, "key")

    def _bucket_id(self, entry):
        """Returns the file object version bucket ID i.e associated bucket."""
        return self.get_field(entry, "bucket_id")

    def _file_id(self, entry):
        """Returns the file object version file ID i.e associated file."""
        return self.get_field(entry, "file_id")

    def _mimetype(self, entry):
        """Returns the file object version mimetype."""
        return self.get_field(entry, "mimetype")

    def _is_head(self, entry):
        """Returns if the file bucket is head i.e the latest."""
        return self.get_field(entry, "is_head")
