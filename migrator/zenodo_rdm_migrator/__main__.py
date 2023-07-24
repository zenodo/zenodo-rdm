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
    ActionStreamDefinition,
    AwardsStreamDefinition,
    CommunitiesStreamDefinition,
    DraftStreamDefinition,
    FilesStreamDefinition,
    FundersStreamDefinition,
    OAuthClientStreamDefinition,
    OAuthServerStreamDefinition,
    RecordStreamDefinition,
    RequestStreamDefinition,
    UserStreamDefinition,
)

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1].lower() in ("--help", "-h"):
        print(f"Usage: {sys.argv[0]} CONFIG_FILE")
        exit(0)

    runner = Runner(
        stream_definitions=[
            ActionStreamDefinition,
            UserStreamDefinition,
            FilesStreamDefinition,
            CommunitiesStreamDefinition,
            RecordStreamDefinition,
            DraftStreamDefinition,
            RequestStreamDefinition,
            FundersStreamDefinition,
            AwardsStreamDefinition,
            OAuthClientStreamDefinition,
            OAuthServerStreamDefinition,
        ],
        config_filepath=sys.argv[1],
    )

    # Now we run the rest of the streams
    runner.run()
