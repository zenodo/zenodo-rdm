# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Utils methods."""

import importlib.resources as pkg_resources
import json

from . import data


def _load_json(filename):
    """Loads a json file."""
    with pkg_resources.open_text(data, filename) as raw_data:
        loaded = json.load(raw_data)
    return loaded
