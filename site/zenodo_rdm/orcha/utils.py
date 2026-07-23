# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Orcha related helpers."""
import time

from invenio_app_rdm.orcha.views import _orcha_client, _workflow_token

FUNDING_CHECK_INSTRUCTIONS = """
    Given a record's title and description, and an EU grant's official description,
    determine whether the record is plausibly related to the grant.

    A record matches if it shares the same research domain, methodology,
    or outputs as the grant.

    Return:
    - match: True if the record is plausibly related to the grant, False otherwise
    - message: a one-sentence explanation of your decision
"""

def run_funding_relevance_workflow(metadata, award_description, rule=""):
    """Run the funding relevance LLM workflow, returning the result dict or {} on timeout."""
    client = _orcha_client()
    token = _workflow_token(client)
    response = client.trigger_workflow(
        payload={
            "workflow_type": "check_funding_relevance",
            "params": {
                "metadata": metadata,
                "award_description": award_description,
                "rule": rule or FUNDING_CHECK_INSTRUCTIONS,
            },
        },
        token=token,
    )
    workflow_id = response["public_id"]
    # poll for result using a scoped token
    workflow_token = _workflow_token(client, workflow_id)
    # Poll until done
    for _ in range(20):
        time.sleep(3)
        data = client.get_workflow(workflow_id, workflow_token)
        if data["status"] in ("success", "error"):
            return data.get("result") or {}
    return {}
