# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator communities transformers."""

from invenio_rdm_migrator.streams.files import FilesTransform

from .entries.files import (
    ZenodoFilesBucketEntry,
    ZenodoFilesInstanceEntry,
    ZenodoFilesObjectVersionEntry,
)


class ZenodoFilesTransform(FilesTransform):
    """Zenodo to RDM Files class for data transformation."""

    def _bucket(self, entry):
        """Transform the bucket."""
        return ZenodoFilesBucketEntry().transform(entry)

    def _object_version(self, entry):
        """Transform the object_version."""
        return ZenodoFilesObjectVersionEntry().transform(entry)

    def _file(self, entry):
        """Transform the file."""
        return ZenodoFilesInstanceEntry().transform(entry)
