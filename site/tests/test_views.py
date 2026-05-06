# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test views."""

from datetime import datetime, timedelta

import pytest
from flask.ctx import _cv_request
from flask.globals import request_ctx
from invenio_access.permissions import system_identity
from invenio_cache import current_cache
from invenio_communities.proxies import current_communities
from invenio_search.api import dsl

from zenodo_rdm.theme.api import cache_key
from zenodo_rdm.theme.tasks import warm_frontpage_cache


def test_frontpage_with_dsl_query(test_app, client):
    """Test frontpage renders successfully with DSL query configuration."""
    # Ensure DSL query is configured
    query = test_app.config["ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY"]
    assert isinstance(query, dsl.query.Query)

    # Request the frontpage
    res = client.get("/")
    assert res.status_code == 200


@pytest.fixture()
def frontpage_records(publish_record, minimal_record, community):
    """Publish records that match the frontpage query and feature the community."""
    base = dict(
        minimal_record,
        access={"record": "public", "files": "public"},
        files={"enabled": False},
    )
    published = [
        publish_record(
            dict(
                base,
                metadata=dict(
                    base["metadata"], title=title, resource_type={"id": rtype}
                ),
            ),
            community=community,
        )
        for title, rtype in [("Dataset one", "dataset"), ("Software one", "software")]
    ]

    current_communities.service.featured_create(
        system_identity,
        community.id,
        {"start_date": (datetime.utcnow() - timedelta(days=1)).isoformat()},
    )
    return published


def test_frontpage_cache_warmup(test_app, frontpage_records):
    """Warmup populates the cache with records and featured communities.

    Runs without a request context to mirror the Celery worker, where the task
    is scheduled.
    """
    recent_uploads_key = cache_key("recent-uploads")
    featured_communities_key = cache_key("featured-communities")
    current_cache.delete(recent_uploads_key)
    current_cache.delete(featured_communities_key)

    # pytest-flask auto-pushes a test request context for tests using `app`.
    # Pop it to mirror the Celery worker, which only has an app context.
    popped = []
    while _cv_request.get(None) is not None:
        ctx = request_ctx._get_current_object()
        ctx.pop()
        popped.append(ctx)

    try:
        warm_frontpage_cache()
    finally:
        for ctx in reversed(popped):
            ctx.push()

    cached_records = current_cache.get(recent_uploads_key)
    cached_communities = current_cache.get(featured_communities_key)
    assert len(cached_records) == 2
    assert {r["metadata"]["title"] for r in cached_records} == {
        "Dataset one",
        "Software one",
    }
    assert len(cached_communities) == 1


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
