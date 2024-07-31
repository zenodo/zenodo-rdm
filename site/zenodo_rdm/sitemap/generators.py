# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Sitemap generators."""

import arrow
from flask import current_app, url_for
from invenio_communities.proxies import current_communities
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_search.api import RecordsSearchV2


def _sitemapdtformat(dt_str):
    """Convert a datetime to a W3 Date and Time format.

    Converts the date to a minute-resolution datetime timestamp with a special
    UTC designator 'Z'. See more information at
    https://www.w3.org/TR/NOTE-datetime.
    """
    return arrow.get(dt_str).format("YYYY-MM-DDTHH:mm:ss") + "Z"


def records_generator():
    """Generate the records links."""
    search = (
        RecordsSearchV2(index=records_service.record_cls.index._name)
        .filter("term", **{"parent.is_verified": True})
        .filter("term", deletion_status="P")
        .sort({"updated": "desc"})
        # This is supposedly bad for performance, and we should isntead use
        # the `search_after` and PIT search: https://www.elastic.co/guide/en/elasticsearch/reference/current/paginate-search-results.html#search-after
        .params(preserve_order=True)
        .source(["id", "updated"])
    )

    scheme = current_app.config["SITEMAP_URL_SCHEME"]
    for record in search.scan():
        yield {
            "loc": url_for(
                "invenio_app_rdm_records.record_detail",
                pid_value=record.id,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(record.updated),
        }


def communities_generator():
    """Generate the communities links."""
    search = (
        RecordsSearchV2(index=current_communities.service.record_cls.index._name)
        .filter("term", is_verified=True)
        .filter("term", deletion_status="P")
        .sort({"updated": "desc"})
        # This is supposedly bad for performance, and we should isntead use
        # the `search_after` and PIT search: https://www.elastic.co/guide/en/elasticsearch/reference/current/paginate-search-results.html#search-after
        .params(preserve_order=True)
        .source(["slug", "updated", "metadata.page"])
    )

    scheme = current_app.config["SITEMAP_URL_SCHEME"]
    for community in search.scan():
        yield {
            "loc": url_for(
                "invenio_app_rdm_communities.communities_detail",
                pid_value=community.slug,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(community.updated),
        }
        if "metadata" in community:
            yield {
                "loc": url_for(
                    "invenio_communities.communities_about",
                    pid_value=community.slug,
                    _external=True,
                    _scheme=scheme,
                ),
                "lastmod": _sitemapdtformat(community.updated),
            }


generator_fns = [
    records_generator,
    communities_generator,
]
