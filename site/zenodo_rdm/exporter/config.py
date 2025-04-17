# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter configuration."""

from uuid import UUID

# Similar to legacy exporter: https://github.com/zenodo/zenodo/blob/master/zenodo/modules/exporter/config.py
EXPORTER_BUCKET_UUID = UUID("00000000-0000-0000-0000-000000000001")

EXPORTER_NUMBER_VERSIONS_TO_KEEP = 3
