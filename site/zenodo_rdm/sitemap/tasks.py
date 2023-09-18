# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM Sitemap tasks."""

import itertools

from celery import shared_task
from flask import current_app, render_template, url_for


@shared_task(ignore_results=True)
def update_sitemap_cache(urls=None, max_url_count=None):
    """Update the Sitemap cache."""
    # We need request context to properly generate the external link
    # using url_for. We fix base_url as we want to simulate a
    # request as it looks from an external client, instead of a task.
    siteurl = current_app.config["SITE_UI_URL"]
    with current_app.test_request_context(base_url=siteurl):
        max_url_count = max_url_count or current_app.config["SITEMAP_MAX_URL_COUNT"]
        sitemap = current_app.extensions["zenodo-sitemap"]
        urls = iter(urls or sitemap._generate_all_urls())

        url_scheme = current_app.config["SITEMAP_URL_SCHEME"]

        urls_slice = list(itertools.islice(urls, max_url_count))
        page_n = 0
        sitemap.clear_cache()
        while urls_slice:
            page_n += 1
            page = render_template(
                "zenodo_sitemap/sitemap.xml", urlset=filter(None, urls_slice)
            )
            sitemap.set_cache("sitemap:{page_n}", page)
            urls_slice = list(itertools.islice(urls, max_url_count))

        urlset = [
            {
                "loc": url_for(
                    "zenodo_sitemap.sitemappage",
                    page=pn,
                    _external=True,
                    _scheme=url_scheme,
                )
            }
            for pn in range(1, page_n + 1)
        ]

        index_page = render_template(
            "zenodo_sitemap/sitemapindex.xml", urlset=urlset, url_scheme=url_scheme
        )
        sitemap.set_cache("sitemap:0", index_page)
