# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities for testing partner payloads on the legacy REST API.

Usage: python -m zenodo_rdm.partners "dryad"

"""

import sys

from . import dryad, lory, plazi
from .client import client
from .payloads import rand_bytes_file

PARTNERS = {
    "dryad": dryad,
    "lory": lory,
    "plazi": plazi,
}


if __name__ == "__main__":
    partner = sys.argv[1]

    data = PARTNERS[partner].PAYLOAD
    res = client.create(data, files=[rand_bytes_file("data.txt")])
