# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test OpenAIRE tasks."""


import json
from unittest.mock import call

from invenio_cache.proxies import current_cache

from zenodo_rdm.openaire.tasks import (
    openaire_delete,
    openaire_direct_index,
    retry_openaire_failures,
)
from zenodo_rdm.openaire.utils import openaire_datasource_id, openaire_original_id


def test_openaire_direct_index_task(
    running_app,
    openaire_record,
    openaire_serializer,
    mocked_session,
    openaire_api_endpoint,
    enable_openaire_indexing,
):
    """Test OpenAIRE direct indexing task.

    The test consists in making sure that the expected OpenAIRE API url would be requested with a ``post`` with
    the correct serialized record.
    """
    serialized_record = openaire_serializer.dump_obj(openaire_record.data)

    # Will be executed synchronously in tests
    openaire_direct_index.delay(openaire_record.id)
    post_endpoint = f"{openaire_api_endpoint}/feedObject"
    mocked_session.post.assert_called_once_with(
        post_endpoint, data=json.dumps(serialized_record), timeout=10
    )

    # Assert key is not in cache : means success
    assert not current_cache.cache.has(f"openaire_direct_index:{openaire_record.id}")


def test_openaire_direct_index_task_with_beta(
    running_app,
    openaire_record,
    openaire_serializer,
    mocked_session,
    openaire_api_endpoint,
    enable_openaire_indexing,
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
    post_endpoint = f"{openaire_api_endpoint}/feedObject"
    beta_endpoint = f"{beta_url}/feedObject"
    calls = [
        call(post_endpoint, data=json.dumps(serialized_record), timeout=10),
        call(beta_endpoint, data=json.dumps(serialized_record), timeout=10),
    ]
    mocked_session.post.assert_has_calls(calls)

    # Assert key is not in cache : means success
    assert not current_cache.cache.has(f"openaire_direct_index:{openaire_record.id}")


def test_openaire_retries_task(
    running_app, openaire_record, mocked_session, enable_openaire_indexing
):
    """Test OpenAIRE retry task.

    The test mocks the post request to fail.
    """
    mocked_session.post.side_effect = Exception("An error.")

    # The task will fail multiple times: the first one + N retries (configured)
    openaire_direct_index.delay(openaire_record.id)

    assert current_cache.cache.has(f"openaire_direct_index:{openaire_record.id}")

    # After failing, the cache has is populated with ``openaire_direct_index:<record.id>`` that is picked up by the task ``retry_openaire_failures``
    mocked_session.post.side_effect = None

    # Reset number of calls on ``post`` - this can be used to assess whether openaire indexing executed succesfully
    mocked_session.post.reset_mock()

    # Execute retry task and validate that the direct indexing succeeded
    retry_openaire_failures.delay()

    # Assert post was executed N times
    assert mocked_session.post.called_once()

    # Assert cache does not have the key
    assert not current_cache.cache.has(f"openaire_direct_index:{openaire_record.id}")


def test_openaire_delete_task(
    running_app, openaire_record, mocked_session, enable_openaire_indexing
):
    # Will be executed synchronously in tests
    openaire_delete.delay(openaire_record.id)

    # Assert ``requests.delete`` was executed once
    original_id = openaire_original_id(openaire_record.data)[1]
    datasource_id = openaire_datasource_id(openaire_record.data)
    openaire_url = running_app.app.config["OPENAIRE_API_URL"]
    params = {"originalId": original_id, "collectedFromId": datasource_id}

    mocked_session.delete.assert_called_once_with(openaire_url, data=json.dumps(params))

    # Assert key is not in cache : means success
    assert not current_cache.cache.has(f"openaire_direct_index:{openaire_record.id}")
