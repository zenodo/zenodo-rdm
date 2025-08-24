# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Additional views."""

from flask import Blueprint, current_app, g, render_template
from invenio_communities.proxies import current_communities
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.resources.serializers import UIJSONSerializer
from invenio_records_resources.resources.records.utils import search_preference
from invenio_search.api import dsl

from .decorators import cached_unless_authenticated_or_flashes
from .filters import is_blr_related_record, is_verified_community, is_verified_record


#
# Views
#
@cached_unless_authenticated_or_flashes(timeout=600, key_prefix="frontpage")
def frontpage_view_function():
    """Zenodo frontpage view."""
    search_kwargs = {
        "params": {"sort": "newest", "size": 10},
    }

    query = current_app.config["ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY"]
    if isinstance(query, str):
        search_kwargs["params"]["q"] = query
    elif isinstance(query, dsl.query.Query):
        search_kwargs["extra_filter"] = query

    recent_uploads = current_rdm_records.records_service.search(
        identity=g.identity,
        search_preference=search_preference(),
        expand=False,
        **search_kwargs,
    )

    records_ui = []

    for record in recent_uploads:
        record_ui = UIJSONSerializer().dump_obj(record)
        records_ui.append(record_ui)

    featured_communities = current_communities.service.featured_search(
        identity=g.identity,
        params=None,
        search_preference=search_preference(),
    )

    return render_template(
        current_app.config["THEME_FRONTPAGE_TEMPLATE"],
        show_intro_section=current_app.config["THEME_SHOW_FRONTPAGE_INTRO_SECTION"],
        recent_uploads=records_ui,
        featured_communities=featured_communities,
    )


#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "zenodo_rdm",
        __name__,
        template_folder="./templates",
    )

    # Register template filters
    blueprint.add_app_template_filter(is_blr_related_record)
    blueprint.add_app_template_test(is_verified_record, name="verified_record")
    blueprint.add_app_template_test(is_verified_community, name="verified_community")

    return blueprint
