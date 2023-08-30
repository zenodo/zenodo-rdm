# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy views."""

from functools import wraps

from flask import Blueprint, abort, jsonify, request
from flask.views import MethodView

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


def create_files_rest_bp(app):
    """Create legacy Files-REST blueprint."""
    ext = app.extensions["zenodo-rdm-legacy"]
    return ext.legacy_files_rest_resource.as_blueprint()


#
# Legacy REST API Stubs
#
stub_blueprint = Blueprint("zenodo_rdm_legacy_stub", __name__)


def pass_extra_formats_mimetype(
    from_query_string=None, from_content_type=None, from_accept=None
):
    """Decorator to validate the request's extra formats MIMEType."""
    assert from_content_type or from_accept or from_query_string

    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            mimetype = None
            if from_query_string:
                mimetype = request.args.get("mimetype")
            if not mimetype and from_content_type:
                mimetype = request.headers.get("Content-Type")
            if not mimetype and from_accept:
                mimetype = next((m for m, _ in request.accept_mimetypes), None)
            if not mimetype:
                return abort(400, "Invalid extra format MIMEType.")
            return f(*args, mimetype=mimetype, **kwargs)

        return inner

    return decorator


class StubDepositExtraFormatsResource(MethodView):
    """Deposit extra formats resource."""

    @pass_extra_formats_mimetype(from_query_string=True, from_accept=True)
    def get(self, pid_value, mimetype=None):
        """Get an extra format."""
        return {"message": f'Dummy content for "{mimetype}".'}

    @pass_extra_formats_mimetype(from_content_type=True)
    def put(self, pid_value, mimetype=None):
        """Create or replace an extra format."""
        return {"message": f'Extra format "{mimetype}" updated.'}

    @pass_extra_formats_mimetype(from_content_type=True)
    def delete(self, pid_value, mimetype=None):
        """Delete an extra format."""
        return {"message": f'Extra format "{mimetype}" deleted.'}

    def options(self, pid_value):
        """Get a list of all extra formats."""
        return jsonify([])


class StubRecordExtraFormatsResource(MethodView):
    """Record extra formats resource."""

    @pass_extra_formats_mimetype(from_query_string=True, from_accept=True)
    def get(self, pid_value, mimetype=None):
        """Get extra format."""
        return {"message": f'Dummy content for "{mimetype}".'}

    def options(self, pid_value):
        """Get available extra formats."""
        return jsonify([])


stub_blueprint.add_url_rule(
    "/deposit/depositions/<pid_value>/formats",
    view_func=StubDepositExtraFormatsResource.as_view("draft_extra_formats_stub"),
)

stub_blueprint.add_url_rule(
    "/records/<pid_value>/formats",
    view_func=StubRecordExtraFormatsResource.as_view("record_extra_formats_stub"),
)
