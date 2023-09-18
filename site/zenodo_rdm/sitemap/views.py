# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Redirects for legacy URLs."""

from flask import Blueprint, abort, current_app
from invenio_cache import current_cache

blueprint = Blueprint(
    "zenodo_sitemap",
    __name__,
    url_prefix="",
    template_folder="templates",
    static_folder="static",
)


def _get_cached_or_404(page):
    data = current_cache.get("sitemap:" + str(page))
    if data:
        return current_app.response_class(data, mimetype="text/xml")
    else:
        abort(404)


@blueprint.route(
    "/sitemap.xml",
    methods=[
        "GET",
    ],
)
def sitemapindex():
    """Get the sitemap index."""
    return _get_cached_or_404(0)


@blueprint.route(
    "/sitemap<int:page>.xml",
    methods=[
        "GET",
    ],
)
def sitemappage(page):
    """Get the sitemap page."""
    return _get_cached_or_404(page)
