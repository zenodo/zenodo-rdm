# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
