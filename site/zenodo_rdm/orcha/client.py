# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Orcha client."""

from datetime import datetime, timedelta, timezone

import jwt
import requests
from flask import current_app, g, jsonify
from invenio_files_rest.models import FileInstance
from invenio_rdm_records.proxies import current_rdm_records_service


class OrchaClient:
    """Client for the Orcha AI workflow service."""

    def __init__(self, key_path=None, key_id=None, tenant=None, base_url=None):
        """Initialize client."""
        self.key_path = key_path
        self.key_id = key_id
        self.tenant = tenant
        self.base_url = base_url
        self._private_key = None

    @property
    def private_key(self):
        """Return private key for JWT token generation."""
        if self._private_key is None:
            with open(self.key_path) as f:
                self._private_key = f.read()
        return self._private_key

    def create_token(self, workflow_id=None):
        """Create a JWT token for authentication with the Orcha workflow service.

        Tokens must include the `iss` claim matching the tenant ID, as well as the key-id.
        Optionally include `workflow_id` to scope access.
        """
        token = jwt.encode(
            {
                "iss": self.tenant,
                "workflow_id": workflow_id or "*",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.key_id},
        )
        return token

    def trigger_workflow(self, pid_value):
        """Proxy a workflow request to the ORCHA service.

        In the current implementation, the (first) file's URI is sent to the AI workflow service,
        and the corresponding workflow ID is returned if successful.
        """
        token = self.create_token()
        record = current_rdm_records_service.read_draft(
            g.identity, pid_value, expand=True
        )
        # TODO: if changing permissions on react, also change it in this check
        current_rdm_records_service.require_permission(
            g.identity, "manage", record=record._record
        )
        if not record["files"]:
            return jsonify({"error": "No files found for this draft"}), 404
        # TODO: after adjusting the workflow to receive several files per record, adapt implementation
        entry = next(iter(record["files"]["entries"].values()))
        file_instance = FileInstance.get(entry["id"])

        try:
            response = requests.post(
                self.base_url + "/workflows",
                json={"url": file_instance.uri},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
            workflow_id = response.json()["public_id"]
            return jsonify({"workflow_id": workflow_id}), 200
        except requests.RequestException as exc:
            if isinstance(exc, requests.Timeout):
                return jsonify({"error": "Workflow service timed out."}), 504
            if isinstance(exc, requests.ConnectionError):
                return jsonify({"error": "Workflow service unavailable."}), 503

            response = getattr(exc, "response", None)
            if response is not None and response.status_code in {401, 403}:
                return jsonify({"error": "Workflow service authorization failed."}), 502
            return jsonify({"error": "Failed to trigger workflow"}), 502

    def stream_workflow(self, pid_value, workflow_id):
        """Streams real-time updates for a specified workflow."""
        token = self.create_token(workflow_id)
        logger = current_app.logger

        def generate():
            try:
                with requests.get(
                    f"{self.base_url}/workflows/{workflow_id}/stream?token={token}",
                    stream=True,
                    timeout=(6.05, 15),  # (connect_timeout, read_timeout)
                ) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=None):
                        if chunk:
                            yield chunk
            except requests.exceptions.Timeout:
                logger.exception(
                    "Workflow stream timed out",
                    extra={"workflow_id": workflow_id},
                )
                yield
            except requests.exceptions.RequestException:
                logger.exception(
                    "Failed to stream extraction workflow results",
                    extra={"workflow_id": workflow_id},
                )
                yield

        return current_app.response_class(
            generate(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # necessary for streaming response
            },
        )
