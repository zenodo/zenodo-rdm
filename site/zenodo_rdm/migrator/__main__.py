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
    DraftStreamDefinition,
    FilesStreamDefinition,
    RecordStreamDefinition,
    RequestStreamDefinition,
    UserStreamDefinition,
)

if __name__ == "__main__":
    runner = Runner(
        stream_definitions=[
            UserStreamDefinition,
            FilesStreamDefinition,
            CommunitiesStreamDefinition,
            RecordStreamDefinition,
            DraftStreamDefinition,
            RequestStreamDefinition,
        ],
        config_filepath=sys.argv[1],
    )

    # Now we run the rest of the streams
    runner.run()
