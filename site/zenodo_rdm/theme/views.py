# SPDX-FileCopyrightText: 2023-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Theme views."""

from flask import Blueprint, current_app, render_template

from .api import featured_communities, recent_uploads
from .filters import is_blr_related_record, is_verified_community, is_verified_record


def frontpage_view_function():
    """Zenodo frontpage view."""
    return render_template(
        current_app.config["THEME_FRONTPAGE_TEMPLATE"],
        show_intro_section=current_app.config["THEME_SHOW_FRONTPAGE_INTRO_SECTION"],
        recent_uploads=recent_uploads(),
        featured_communities=featured_communities(),
    )


def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "zenodo_rdm",
        __name__,
        template_folder="../templates",
    )

    blueprint.add_app_template_filter(is_blr_related_record)
    blueprint.add_app_template_test(is_verified_record, name="verified_record")
    blueprint.add_app_template_test(is_verified_community, name="verified_community")

    return blueprint
