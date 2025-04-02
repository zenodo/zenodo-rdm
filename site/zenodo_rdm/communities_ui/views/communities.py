# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2024 CERN.
# Copyright (C) 2019-2022 Northwestern University.
# Copyright (C)      2022 TU Wien.
#
# Invenio App RDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Request views module."""

from flask import g, redirect, request, url_for
from invenio_communities.views.communities import (
    HEADER_PERMISSIONS,
    render_community_theme_template,
)
from invenio_communities.views.decorators import pass_community
from invenio_rdm_records.proxies import (
    current_community_records_service,
    current_rdm_records,
)
from invenio_rdm_records.resources.serializers import UIJSONSerializer
from invenio_records_resources.services.errors import PermissionDeniedError


def publications_metric_blr(results):
    """Publications metric for BLR."""
    resource_types = results._results.aggregations.resource_types.buckets
    valid_pubication_types = [
        "publication-article",
        "publication-book",
        "publication-section",
        "publication-datamanagementplan",
    ]
    publications = 0
    for resource_type in resource_types:
        if resource_type.key in valid_pubication_types:
            publications += resource_type.doc_count
    return publications


def images_metric_blr(results):
    """Images metric for BLR."""
    resource_types = results._results.aggregations.resource_types.buckets
    images = 0
    for resource_type in resource_types:
        if resource_type.key.startswith("image"):
            images += resource_type.doc_count
    return images


def treatments_metric_blr(results):
    """Treatments metric for BLR."""
    resource_types = results._results.aggregations.resource_types.buckets
    for resource_type in resource_types:
        if resource_type.key == "publication-taxonomictreatment":
            return resource_type.doc_count


def tables_metric_blr(results):
    """Tables metric for BLR."""
    resource_types = results._results.aggregations.resource_types.buckets
    for resource_type in resource_types:
        if resource_type.key == "dataset":
            return resource_type.doc_count


METRICS = {
    "total_grants": {
        "name": "total_grants",
        "type": "cardinality",
        "kwargs": {"field": "metadata.funding.award.id"},
    },
    "total_data": {
        "name": "total_data",
        "type": "sum",
        "kwargs": {"field": "files.totalbytes"},
    },
    "total_views": {
        "name": "total_views",
        "type": "sum",
        "kwargs": {"field": "stats.all_versions.unique_views"},
    },
    "total_downloads": {
        "name": "total_downloads",
        "type": "sum",
        "kwargs": {"field": "stats.all_versions.unique_downloads"},
    },
    "resource_types": {
        "name": "resource_types",
        "type": "terms",
        "kwargs": {"field": "metadata.resource_type.id"},
    },
}


THEME_METRICS = {
    "horizon": {"total_data": "total_data", "total_grants": "total_grants"},
    "biosyslit": {
        "total_views": "total_views",
        "total_downloads": "total_downloads",
        "publications": publications_metric_blr,
        "images": images_metric_blr,
        "tables": tables_metric_blr,
        "treatments": treatments_metric_blr,
    },
}


def _get_metric_from_search(result, metric):
    """Get metric from search result."""
    return result._results.aggregations[metric].value


@pass_community(serialize=True)
def communities_home(pid_value, community, community_ui):
    """Community home page."""
    query_params = request.args
    collections_service = current_rdm_records.collections_service
    permissions = community.has_permissions_to(HEADER_PERMISSIONS)
    if not permissions["can_read"]:
        raise PermissionDeniedError()

    theme_enabled = community._record.theme and community._record.theme.get(
        "enabled", False
    )

    if query_params or not theme_enabled:
        url = url_for(
            "invenio_app_rdm_communities.communities_detail",
            pid_value=community.data["slug"],
            **request.args,
        )
        return redirect(url)

    if theme_enabled:
        recent_uploads = current_community_records_service.search(
            community_id=pid_value,
            identity=g.identity,
            params={"sort": "newest", "size": 3, "metrics": METRICS},
            expand=True,
        )

        collections = collections_service.list_trees(g.identity, community.id, depth=0)

        # TODO resultitem does not expose aggregations except labelled facets
        metrics = {
            "total_records": recent_uploads.total,
        }
        for metric, getter in THEME_METRICS.get(
            community._record.theme["brand"], {}
        ).items():
            if type(getter) == str:
                metrics[metric] = _get_metric_from_search(recent_uploads, getter)
            else:
                metrics[metric] = getter(recent_uploads) or 0

        records_ui = UIJSONSerializer().dump_list(recent_uploads.to_dict())["hits"][
            "hits"
        ]

        return render_community_theme_template(
            "invenio_communities/details/home/index.html",
            theme=community_ui.get("theme", {}),
            community=community_ui,
            permissions=permissions,
            records=records_ui,
            metrics=metrics,
            collections=collections.to_dict(),
        )
