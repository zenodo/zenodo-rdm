# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter views."""

from flask import Blueprint, Response, abort, current_app
from invenio_files_rest.models import ObjectVersion, as_bucket

blueprint = Blueprint(
    # TODO: No `zenodo_` prefix?
    "zenodo_exporter",
    __name__,
    # url_prefix="/exporter",
)


def _get_bucket():
    bucket_uuid = current_app.config["EXPORTER_BUCKET_UUID"]
    bucket = as_bucket(bucket_uuid)
    if not bucket:
        abort(404, description="Bucket not found")
    return bucket


@blueprint.route("/exporter")
def list_object_versions():
    """List object versions and the updated dates."""

    bucket = _get_bucket()
    ovs = ObjectVersion.get_by_bucket(bucket).all()

    # TODO: `created` instead of `updated`?
    # TODO: `isoformat()` returns time at GMT without TZ information; is it OK?
    return {ov.key: ov.updated.isoformat() for ov in ovs}


# Remark: using `path` and not `string` to support namespacing via slashes in `key`.
# Remark: exporter files are public and do not require permission.
@blueprint.route("/exporter/<path:key>")
def get_object_version_content(key):
    """Download the content of a specific object version."""
    bucket = _get_bucket()

    # TODO: Sanitize key input?
    # ObjectVersion.validate_key(key)

    ov = ObjectVersion.get(bucket, key)
    if not ov:
        abort(404, description="Key not found")

    return ov.send_file()
