# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Routes for Orcha."""

from datetime import datetime, timedelta, timezone

import jwt
import requests
from flask import Blueprint, current_app, g, jsonify
from invenio_files_rest.errors import InvalidOperationError
from invenio_rdm_records.proxies import current_rdm_records
from invenio_records_resources.services.errors import PermissionDeniedError

from .client import OrchaClient

blueprint = Blueprint("orcha", __name__)


def get_orcha_client():
    """Instantiate OrchaClient from app config."""
    return OrchaClient(
        key_path=current_app.config["ZENODO_ORCHA_KEY_PATH"],
        key_id=current_app.config["ZENODO_ORCHA_KID"],
        tenant=current_app.config["ZENODO_ORCHA_TENANT"],
        base_url=current_app.config["ZENODO_ORCHA_URL"],
        ssl_verify=current_app.config.get("ZENODO_ORCHA_SSL_VERIFY", True),
    )


def get_file_data(pid_value):
    """Get file uri/url and filename from the pid."""

    def convert_eos_path(path):
        """Convert EOS redirect paths to HTTP URLs."""
        import re

        pattern = r"/eos_storage/http/([^/]+)/(\d+)(/.+)"
        match = re.match(pattern, path)
        if match:
            host, port, rest = match.groups()
            return f"http://{host}:{port}{rest}"
        return path

    permission = current_app.config["ZENODO_ORCHA_PERMISSION"]
    if not permission():
        raise PermissionDeniedError()
    service = current_rdm_records.records_service
    draft = service.config.draft_cls.pid.resolve(pid_value, registered_only=False)
    service.require_permission(g.identity, "manage", record=draft)
    if not (draft.files and draft.files.entries):
        raise InvalidOperationError(description="Draft has no files")

    # TODO: after adjusting the workflow to receive several files per record, adapt implementation
    first_file_name = next(iter(draft.files.entries))
    record_file = draft.files[first_file_name]
    object_version = record_file.object_version
    file_instance = object_version.file

    if current_app.config["IS_LOCAL_DEV"]:
        url = file_instance.uri
    else:
        storage_factory = current_app.config.get("FILES_REST_STORAGE_FACTORY")
        storage = storage_factory(
            fileinstance=file_instance,
            default_location=object_version.bucket.location.uri,
        )
        url_to_reconstruct = storage._get_eos_redirect_path()
        url = convert_eos_path(url_to_reconstruct)

    return {
        "url": url,
        "filename": first_file_name,
    }


@blueprint.route("/uploads/<pid_value>/orcha", methods=["POST"])
def get_workflow_stream_url(pid_value):
    """Proxy a workflow request to the ORCHA service.

    In the current implementation, the (first) file's URI is sent to the AI workflow service,
    and the corresponding workflow ID is returned if successful.
    """
    orcha = get_orcha_client()
    trigger_token = create_token(orcha)
    payload = get_file_data(pid_value)

    try:
        response = orcha.trigger_workflow(payload, trigger_token)
        workflow_id = response["public_id"]
        stream_token = create_token(orcha, workflow_id)
        return (
            jsonify(
                {
                    "workflowId": workflow_id,
                    "streamUrl": orcha.stream_url(workflow_id, stream_token),
                }
            ),
            200,
        )
    except requests.Timeout:
        return jsonify({"error": "Workflow service timed out."}), 504
    except requests.ConnectionError:
        return jsonify({"error": "Workflow service unavailable."}), 503
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in {401, 403}:
            return jsonify({"error": "Workflow service authorization failed."}), 502
        return jsonify({"error": "Failed to trigger workflow"}), 502


def create_token(client, workflow_id=None, expiry=timedelta(minutes=30)):
    """Create a JWT token for authentication with the Orcha workflow service.

    Tokens must include the `iss` claim matching the tenant ID, as well as the key-id.
    Optionally include `workflow_id` to scope access.
    """
    token = jwt.encode(
        {
            "iss": client.tenant,
            "workflow_id": workflow_id or "*",
            "exp": datetime.now(timezone.utc) + expiry,
        },
        client.private_key,
        algorithm="RS256",
        headers={"kid": client.key_id},
    )
    return token
