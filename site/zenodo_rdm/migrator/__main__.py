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
    FileStream,
    RecordStreamDefinition,
    RequestStreamDefinition,
    UserStreamDefinition,
)

if __name__ == "__main__":
    runner = Runner(
        stream_definitions=[
            UserStreamDefinition,
            CommunitiesStreamDefinition,
            RecordStreamDefinition,
            DraftStreamDefinition,
            RequestStreamDefinition,
        ],
        config_filepath=sys.argv[1],
    )

    # TODO: This could be integrate into the main runner above
    cfg = runner._read_config(sys.argv[1])
    FileStream(
        tmp_dir=cfg["files"]["load"]["tmp_dir"],
        db_uri=cfg["files"]["load"]["db_uri"],
    ).run()

    # Now we run the rest of the streams
    runner.run()
