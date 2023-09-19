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
    AffiliationsStreamDefinition,
    AwardsStreamDefinition,
    CommunitiesStreamDefinition,
    DeletedRecordStreamDefinition,
    DraftStreamDefinition,
    FilesStreamDefinition,
    FundersStreamDefinition,
    GitHubReleasesStreamDefinition,
    GitHubRepositoriesStreamDefinition,
    NamesStreamDefinition,
    OAuthClientStreamDefinition,
    OAuthServerClientStreamDefinition,
    OAuthServerTokenStreamDefinition,
    RecordStreamDefinition,
    RequestStreamDefinition,
    UserStreamDefinition,
    VersionStateStreamDefinition,
    WebhookEventsStreamDefinition,
)

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1].lower() in ("--help", "-h"):
        print(f"Usage: {sys.argv[0]} CONFIG_FILE")
        exit(0)

    runner = Runner(
        stream_definitions=[
            ActionStreamDefinition,
            FundersStreamDefinition,
            AwardsStreamDefinition,
            AffiliationsStreamDefinition,
            NamesStreamDefinition,
            UserStreamDefinition,
            OAuthClientStreamDefinition,
            OAuthServerClientStreamDefinition,
            OAuthServerTokenStreamDefinition,
            FilesStreamDefinition,
            CommunitiesStreamDefinition,
            RecordStreamDefinition,
            DraftStreamDefinition,
            DeletedRecordStreamDefinition,
            VersionStateStreamDefinition,
            RequestStreamDefinition,
            WebhookEventsStreamDefinition,
            GitHubReleasesStreamDefinition,
            GitHubRepositoriesStreamDefinition,
        ],
        config_filepath=sys.argv[1],
    )

    # Now we run the rest of the streams
    runner.run()
