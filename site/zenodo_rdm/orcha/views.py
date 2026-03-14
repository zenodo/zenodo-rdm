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
from invenio_files_rest.models import FileInstance
from invenio_rdm_records.proxies import current_rdm_records_service

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


@blueprint.route("/uploads/<pid_value>/orcha", methods=["POST"])
def get_workflow_stream_url(pid_value):
    """Proxy a workflow request to the ORCHA service.

    In the current implementation, the (first) file's URI is sent to the AI workflow service,
    and the corresponding workflow ID is returned if successful.
    """
    record = current_rdm_records_service.read_draft(g.identity, pid_value, expand=True)
    # TODO: if changing permissions on react, also change it in this check
    current_rdm_records_service.require_permission(
        g.identity, "manage", record=record._record
    )
    if not (record["files"] and record["files"].get("entries", {})):
        return jsonify({"error": "No files found for this draft"}), 404
    # TODO: after adjusting the workflow to receive several files per record, adapt implementation
    entry = next(iter(record["files"]["entries"].values()))
    file_instance = FileInstance.get(entry["id"])

    orcha = get_orcha_client()
    trigger_token = create_token(orcha)
    payload = {"url": file_instance.uri}

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
