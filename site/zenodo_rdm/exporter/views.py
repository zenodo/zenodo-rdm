# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter views."""

import arrow
from flask import Blueprint, abort, current_app, url_for
from invenio_files_rest.models import ObjectVersion, as_bucket

blueprint = Blueprint(
    "exporter",
    __name__,
)


def _get_bucket():
    bucket_uuid = current_app.config["EXPORTER_BUCKET_UUID"]
    bucket = as_bucket(bucket_uuid)
    if not bucket:
        abort(404, description="Bucket not found")
    return bucket


@blueprint.route("/exporter")
def list_object_versions():
    """List object versions grouped by keys, and with list of create dates and version IDs."""
    bucket = _get_bucket()
    ovs = ObjectVersion.get_by_bucket(bucket, versions=True).all()
    response = {}
    for ov in ovs:
        ov_response = {
            "version_id": ov.version_id,
            "created": arrow.get(ov.created).to("utc").isoformat(),
            "is_head": ov.is_head,
            "size": ov.file.size,
            "checksum": ov.file.checksum,
            "links": {
                "self": url_for(
                    "exporter.get_object_version_content",
                    key=ov.key,
                    version_id=ov.version_id,
                    _external=True,
                ),
            },
        }
        if ov.is_head:
            ov_response["links"]["self_head"] = url_for(
                "exporter.get_object_version_content",
                key=ov.key,
                _external=True,
            )
        if ov.key not in response:
            response[ov.key] = []
        response[ov.key].append(ov_response)
    return response


# Remark: using `path` and not `string` to support namespacing via slashes in `key`.
# Remark: exporter files are public (generated with `AnonymousIdentity`) and do not require permission.
@blueprint.route("/exporter/<path:key>")
@blueprint.route("/exporter/<path:key>/<uuid:version_id>")
def get_object_version_content(key, version_id=None):
    """Download the content of an object version for a given key and an optional version ID."""
    bucket = _get_bucket()
    ov = ObjectVersion.get(bucket, key, version_id)
    if not ov:
        abort(404, description="ObjectVersion not found")
    return ov.send_file()
