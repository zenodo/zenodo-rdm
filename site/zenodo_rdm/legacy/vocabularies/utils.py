# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Utils methods."""

import importlib.resources as pkg_resources
import json

from zenodo_rdm.legacy.vocabularies import data


def _load_json(filename):
    """Loads a json file."""
    with pkg_resources.open_text(data, filename) as raw_data:
        loaded = json.load(raw_data)
    return loaded
