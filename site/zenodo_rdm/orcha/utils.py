# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Orcha related helpers."""

import time

import requests
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_app_rdm.orcha.views import (
    _file_download_url,
    _orcha_client,
    _workflow_token,
)

FUNDING_CHECK_INSTRUCTIONS = """
    Given a record's title and description, and an EU grant's official description,
    determine whether the record is plausibly related to the grant.

    A record matches if it shares the same research domain, methodology,
    or outputs as the grant.

    Return:
    - match: True if the record is plausibly related to the grant, False otherwise
    - message: a one-sentence explanation of your decision
"""


def _get_orcha_client_token():
    try:
        client = _orcha_client()
        token = _workflow_token(client)
        return client, token
    except RuntimeError as e:
        current_app.logger.error("Orcha misconfiguration: %s", e)
        raise


def _trigger_workflow(client, token, payload):
    try:
        response = client.trigger_workflow(
            payload=payload,
            token=token,
        )
        return response
    except requests.ConnectionError:
        current_app.logger.error("Cannot reach Orcha at %s", client.base_url)
        raise
    except requests.Timeout:
        current_app.logger.error(
            "Orcha request timed out (base_url=%s)", client.base_url
        )
        raise
    except requests.HTTPError as e:
        status = (
            e.response.status_code
            if e.response is not None
            else "(missing status code)"
        )
        body = e.response.text if e.response is not None else ""
        if status in (401, 403):
            current_app.logger.error(
                "Orcha auth failure (HTTP %s), check tenant config",
                status,
            )
        elif status in (400, 422):
            current_app.logger.error(
                "Orcha rejected check payload (HTTP %s): %s", status, body
            )
        else:
            current_app.logger.error("Orcha failed HTTP %s: %s", status, body)
        raise


def _poll_to_return_result(client, workflow_id, poll_until=20, sleep_time=3):
    workflow_token = _workflow_token(client, workflow_id)
    for _ in range(poll_until):
        time.sleep(sleep_time)
        data = client.get_workflow(workflow_id, workflow_token)
        if data["status"] in ("success", "error"):
            result = data.get("result") or {}
            result["workflow_id"] = workflow_id
            return data["status"], result
    return "timeout", {}


def run_funding_relevance_workflow(metadata, award_description, rule=""):
    """Run the funding relevance LLM workflow, returning the result dict or {} on timeout."""
    client, token = _get_orcha_client_token()
    payload = {
        "workflow_type": "check_funding_relevance",
        "params": {
            "metadata": metadata,
            "award_description": award_description,
            "rule": rule or FUNDING_CHECK_INSTRUCTIONS,
        },
    }
    response = _trigger_workflow(client, token, payload)
    workflow_id = response["public_id"]
    # poll for result using a scoped token, until done
    _status, result = _poll_to_return_result(client, workflow_id)
    return result


def run_compare_metadata_workflow(pid_value, file_key, metadata):
    """Run the compare_metadata LLM workflow, returning the result dict or {} on timeout."""
    client, token = _get_orcha_client_token()
    file_url = _file_download_url(
        pid_value, client, key=file_key, identity=system_identity
    )
    payload = {
        "workflow_type": "compare_metadata",
        "params": {
            "url": file_url,
            "metadata": metadata,
        },
    }
    response = _trigger_workflow(client, token, payload)
    workflow_id = response["public_id"]
    return _poll_to_return_result(client, workflow_id, poll_until=40)
