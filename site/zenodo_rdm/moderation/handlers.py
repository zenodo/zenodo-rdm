# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Handlers for ZenodoRDM Moderation."""

from flask import current_app
from invenio_access.permissions import system_identity


class BaseScoreHandler:
    """Base handler to calculate moderation scores based on rules."""

    def __init__(self, rules=None):
        """Initialize the score handler with a set of rules."""
        self.rules = rules

    def run(self, identity, draft=None, record=None):
        """Calculate the moderation score for a given record or draft."""
        score = 0
        rules = current_app.config[self.rules]
        for rule in rules:
            score += rule(identity, draft=draft, record=record)

        current_app.logger.warning(
            f"Moderation score for record - [{record.metadata['title']}]: {score}"
        )


class RecordScoreHandler(BaseScoreHandler):
    """Handler for calculating scores for records."""

    def __init__(self):
        """Initialize with record moderation rules."""
        super().__init__(rules="RDM_RECORD_MODERATION_SCORE_RULES")

    def publish(self, identity, record):
        """Calculate and log the score when a record is published."""
        score = self.run(identity, record=record)
        current_app.logger.info(
            f"Record {record.metadata['title']} published with moderation score: {score}"
        )


class CommunityScoreHandler(BaseScoreHandler):
    """Handler for calculating scores for communities."""

    def __init__(self):
        """Initialize with community moderation rules."""
        super().__init__(rules="COMMUNITY_MODERATION_SCORE_RULES")

    def update(self, identity, community):
        """Calculate and log the score when a community is updated."""
        score = self.run(identity, record=community)
        current_app.logger.info(
            f"Community {community.metadata['title']} updated with moderation score: {score}"
        )

    def create(self, identity, community):
        """Calculate and log the score when a community is created."""
        score = self.run(identity, record=community)
        current_app.logger.info(
            f"Community {community.metadata['title']} created with moderation score: {score}"
        )
