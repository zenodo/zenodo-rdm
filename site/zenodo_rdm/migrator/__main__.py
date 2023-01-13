# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Implements the main function to run the migrator."""

import sys

from invenio_rdm_migrator.streams import Runner

from .stream import (
    CommunitiesStreamDefinition,
    RecordStreamDefinition,
    UserStreamDefinition,
)

if __name__ == "__main__":

    runner = Runner(
        stream_definitions=[
            UserStreamDefinition,
            CommunitiesStreamDefinition,
            RecordStreamDefinition,
        ],
        config_filepath=sys.argv[1],
    )
    runner.run()
