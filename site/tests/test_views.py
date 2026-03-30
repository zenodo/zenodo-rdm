# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test views."""

from invenio_search.api import dsl


def test_frontpage_with_dsl_query(test_app, client):
    """Test frontpage renders successfully with DSL query configuration."""
    # Ensure DSL query is configured
    query = test_app.config["ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY"]
    assert isinstance(query, dsl.query.Query)

    # Request the frontpage
    res = client.get("/")
    assert res.status_code == 200


def test_frontpage_with_string_query(test_app, client, set_app_config_fn_scoped):
    """Test frontpage works with legacy string query configuration."""
    # Override config to use string query for backwards compatibility test
    set_app_config_fn_scoped(
        {
            "ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY": "type:(dataset OR software) AND access.files:public"
        }
    )

    # Request the frontpage
    res = client.get("/")
    assert res.status_code == 200
