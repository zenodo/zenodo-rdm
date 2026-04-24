# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Theme API."""

from flask import current_app
from flask_principal import AnonymousIdentity
from invenio_access.permissions import any_user
from invenio_cache import current_cache
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.resources.serializers import UIJSONSerializer
from invenio_search.api import dsl


def cache_key(name):
    """Build a deploy-aware frontpage cache key."""
    timestamp = current_app.config.get("IMAGE_BUILD_TIMESTAMP", "")
    return f"frontpage:{timestamp}:{name}"


def recent_uploads(refresh_cache=False):
    """Return cached recent upload records."""
    key = cache_key("recent-uploads")

    if not refresh_cache:
        records = current_cache.get(key)
        if records is not None:
            return records

    identity = AnonymousIdentity()
    identity.provides.add(any_user)
    search_kwargs = {
        "params": {"sort": "newest", "size": 10},
    }

    query = current_app.config["ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY"]
    if isinstance(query, str):
        search_kwargs["params"]["q"] = query
    elif isinstance(query, dsl.query.Query):
        search_kwargs["extra_filter"] = query

    recent_records = current_rdm_records.records_service.search(
        identity=identity,
        search_preference=None,
        expand=False,
        **search_kwargs,
    )

    serializer = UIJSONSerializer()
    records = [serializer.dump_obj(record) for record in recent_records]

    current_cache.set(
        key,
        records,
        timeout=current_app.config["ZENODO_FRONTPAGE_CACHE_TIMEOUT"],
    )
    return records


def featured_communities(refresh_cache=False):
    """Return cached featured communities."""
    key = cache_key("featured-communities")

    if not refresh_cache:
        communities = current_cache.get(key)
        if communities is not None:
            return communities

    identity = AnonymousIdentity()
    identity.provides.add(any_user)
    communities = current_communities.service.featured_search(
        identity=identity,
        params=None,
        search_preference=None,
    )
    communities = list(communities)

    current_cache.set(
        key,
        communities,
        timeout=current_app.config["ZENODO_FRONTPAGE_CACHE_TIMEOUT"],
    )
    return communities
