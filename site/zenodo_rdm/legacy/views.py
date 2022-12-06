# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy views."""

from flask import Blueprint

blueprint = Blueprint("zenodo_rdm_legacy", __name__)


@blueprint.record_once
def init(state):
    """Init app."""
    app = state.app
    sregistry = app.extensions["invenio-records-resources"].registry
    ext = app.extensions["zenodo-rdm-legacy"]
    sregistry.register(ext.legacy_records_service, service_id="legacy-records")
    sregistry.register(
        ext.legacy_records_service.draft_files, service_id="legacy-draft-files"
    )


def create_legacy_records_bp(app):
    """Create legacy records blueprint."""
    ext = app.extensions["zenodo-rdm-legacy"]
    return ext.legacy_records_resource.as_blueprint()


def create_draft_files_bp(app):
    """Create legacy draft files blueprint."""
    ext = app.extensions["zenodo-rdm-legacy"]
    return ext.legacy_draft_files_resource.as_blueprint()
