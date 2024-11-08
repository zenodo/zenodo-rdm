# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test ModerationQuery model class."""

from invenio_db import db
from invenio_search import current_search_client
from zenodo_rdm.moderation.models import ModerationQuery
from zenodo_rdm.moderation.rules import match_query_rule
from zenodo_rdm.api import ZenodoRDMRecord

def test_moderation_query_creation(app):
    """Test to create and index a ModerationQuery."""
    with app.app_context():
        query_string = "metadata.title:SimpleTest"
        notes = "test query"
        score = 5
        active = True

        query = ModerationQuery.create(
            query_string, ZenodoRDMRecord, notes=notes, score=score, active=active
        )
        db.session.commit()

        # Check if query attributes are set correctly
        assert all(
            [
                query.query_string == query_string,
                query.notes == notes,
                query.score == score,
                query.active == active,
            ]
        )

#TODO: Add test for matching query