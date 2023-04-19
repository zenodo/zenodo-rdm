# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator transformers."""


from .bucket import ZenodoFilesBucketEntry
from .file import ZenodoFilesInstanceEntry
from .object_version import ZenodoFilesObjectVersionEntry

__all__ = (
    ZenodoFilesBucketEntry,
    ZenodoFilesInstanceEntry,
    ZenodoFilesObjectVersionEntry,
)
