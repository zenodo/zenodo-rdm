# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test OpenAIRE tasks."""


import json
from unittest.mock import call

from zenodo_rdm.openaire.tasks import openaire_direct_index


def test_openaire_direct_index_task(
    running_app,
    openaire_record,
    openaire_serializer,
    mocked_session,
    openaire_api_endpoint,
):
    """Test OpenAIRE direct indexing task.

    The test consists in making sure that the expected OpenAIRE API url would be requested with a ``post`` with
    the correct serialized record.
    """
    serialized_record = openaire_serializer.dump_obj(openaire_record.data)

    # Will be executed synchronously in tests
    openaire_direct_index.delay(openaire_record.id)
    mocked_session.post.assert_called_once_with(
        openaire_api_endpoint, data=json.dumps(serialized_record), timeout=10
    )


def test_openaire_direct_index_task_with_beta(
    running_app,
    openaire_record,
    openaire_serializer,
    mocked_session,
    openaire_api_endpoint,
    monkeypatch,
):
    """Test OpenAIRE direct indexing task but also hit BETA API."""
    # Only for this test, modify record service components
    beta_url = "https://beta.services.openaire.eu/provision/mvc/api/results"
    monkeypatch.setitem(
        running_app.app.config,
        "OPENAIRE_API_URL_BETA",
        beta_url,
    )
    serialized_record = openaire_serializer.dump_obj(openaire_record.data)

    # Will be executed synchronously in tests
    openaire_direct_index.delay(openaire_record.id)

    # Assert two ``post`` requests were issued: one to production and one to beta
    beta_endpoint = f"{beta_url}/feedObject"
    calls = [
        call(openaire_api_endpoint, data=json.dumps(serialized_record), timeout=10),
        call(beta_endpoint, data=json.dumps(serialized_record), timeout=10),
    ]
    mocked_session.post.assert_has_calls(calls)
