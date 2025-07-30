# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Sitemap sections for ZenodoRDM using invenio-sitemap."""

from invenio_base import invenio_url_for
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_search.api import RecordsSearchV2
from invenio_sitemap import SitemapSection, format_to_w3c


class RecordsSection(SitemapSection):
    """Defines the Sitemap entries for Records."""

    def iter_entities(self):
        """Iterate over objects."""
        return (
            RecordsSearchV2(index=current_rdm_records_service.record_cls.index._name)
            .filter("term", **{"parent.is_verified": True})
            .filter("term", deletion_status="P")
            .sort({"updated": "desc"})
            .params(preserve_order=True)
            .source(["id", "updated"])
            .scan()
        )

    def to_dict(self, entity):
        """To dict used in sitemap."""
        return {
            "loc": invenio_url_for(
                "invenio_app_rdm_records.record_detail", pid_value=entity["id"]
            ),
            "lastmod": format_to_w3c(entity["updated"]),
        }


class CommunitiesSection(SitemapSection):
    """Defines the Sitemap entries for Communities."""

    def iter_entities(self):
        """Iterate over objects."""
        communities_scan = (
            RecordsSearchV2(index=current_communities.service.record_cls.index._name)
            .filter("term", is_verified=True)
            .filter("term", deletion_status="P")
            .sort({"updated": "desc"})
            .params(preserve_order=True)
            .source(["slug", "updated", "metadata.page"])
            .scan()
        )

        for community in communities_scan:
            yield {
                "slug": community.slug,
                "updated": community.updated,
                "loc": invenio_url_for(
                    "invenio_app_rdm_communities.communities_detail",
                    pid_value=community.slug,
                ),
            }

            if "page" in community.get("metadata", {}):
                yield {
                    "slug": community.slug,
                    "updated": community.updated,
                    "loc": invenio_url_for(
                        "invenio_communities.communities_about",
                        pid_value=community.slug,
                    ),
                }

    def to_dict(self, entity):
        """To dict used in sitemap."""
        return {
            "loc": entity["loc"],
            "lastmod": format_to_w3c(entity["updated"]),
        }
