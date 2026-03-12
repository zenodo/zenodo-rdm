# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Routes for Orcha."""

from flask import Blueprint

from .client import OrchaClient


def create_blueprint(app):
    """Create blueprint."""
    blueprint = Blueprint("orcha", __name__)

    if not app.config.get("ZENODO_ORCHA_INTEGRATION_ENABLED", False):
        return blueprint

    orcha = OrchaClient(
        key_path=app.config["ZENODO_ORCHA_KEY_PATH"],
        key_id=app.config["ZENODO_ORCHA_KID"],
        tenant=app.config["ZENODO_ORCHA_TENANT"],
        base_url=app.config["ZENODO_ORCHA_URL"],
    )
    orcha_routes = app.config["ZENODO_ORCHA_ROUTES"]

    blueprint.add_url_rule(
        rule=orcha_routes["trigger_workflow"],
        view_func=orcha.trigger_workflow,
        methods=["POST"],
    )

    blueprint.add_url_rule(
        rule=orcha_routes["stream_workflow"],
        view_func=orcha.stream_workflow,
    )

    return blueprint
