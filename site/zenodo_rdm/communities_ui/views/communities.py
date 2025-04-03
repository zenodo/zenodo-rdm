# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2024 CERN.
# Copyright (C) 2019-2022 Northwestern University.
# Copyright (C)      2022 TU Wien.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Community custom views."""

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

from .metrics_config import THEME_METRICS, THEME_METRICS_QUERY


def _get_metric_from_search(result, accessor):
    """Get metric from search result."""
    value = result._results.aggregations
    keys = accessor.split(".")
    for key in keys:
        value = value[key]
    return value


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
            params={
                "sort": "newest",
                "size": 3,
                "metrics": THEME_METRICS_QUERY[community._record.theme["brand"]],
            },
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
