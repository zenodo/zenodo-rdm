# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test deposit metadata (REST API)."""

import json

import dictdiffer
import pytest


def test_invalid_create(test_app, client_with_login, deposit_url, headers):
    """Test invalid deposit creation.

    Test ported from https://github.com/zenodo/zenodo/blob/master/tests/unit/deposit/test_api_metadata.py.
    """
    client = client_with_login

    # Invalid deposits.
    cases = [
        dict(unknownkey="data", metadata={}),
    ]

    for case in cases:
        res = client.post(deposit_url, data=json.dumps(case), headers=headers)
        assert res.status_code == 400, case

    # No deposits were created
    res = client.get(deposit_url, headers=headers)
    assert len(res.json) == 0


def test_input_output(
    test_app,
    client_with_login,
    headers,
    deposit_url,
    test_data,
    expected_record_metadata,
):
    """Rough validation of input against output data.

    Test ported from https://github.com/zenodo/zenodo/blob/master/tests/unit/deposit/test_api_metadata.py.
    """
    client = client_with_login

    # Create
    res = client.post(deposit_url, json=test_data, headers=headers)
    assert res.status_code == 201
    links = res.json["links"]

    # Get serialization.
    res = client.get(links["self"], headers=headers)
    assert res.status_code == 200
    data = res.json

    # - fix known differences.
    # DOI and recid have 2 as control number, since Concept DOI/recid are
    # registered first
    recid = data["id"]
    expected_record_metadata.update(
        {
            "prereserve_doi": {"doi": f"10.5281/zenodo.{recid}", "recid": recid},
        }
    )

    differences = list(
        dictdiffer.diff(
            data["metadata"],
            expected_record_metadata,
            # doi is returned as a top level key (and not inside metadata)
            ignore={"doi"},
        )
    )

    assert not differences


@pytest.mark.parametrize(
    "related_identifiers,expected_field,expected_message",
    [
        (
            "not-a-list",
            "metadata.related_identifiers",
            "related_identifiers must be a list",
        ),
        (
            ["not-a-dict"],
            "metadata.related_identifiers.0",
            "Each related identifier must be an object",
        ),
        (
            [{"identifier": "10.1234/foo", "relation": 123}],
            "metadata.related_identifiers.0.relation",
            "relation must be a string",
        ),
    ],
)
def test_malformed_related_identifiers(
    test_app,
    client_with_login,
    deposit_url,
    headers,
    related_identifiers,
    expected_field,
    expected_message,
):
    """Test malformed related_identifiers validation."""
    data = {
        "metadata": {
            "title": "Test",
            "upload_type": "dataset",
            "description": "Test description",
            "creators": [{"name": "Test User"}],
            "related_identifiers": related_identifiers,
        }
    }
    res = client_with_login.post(deposit_url, json=data, headers=headers)
    assert res.status_code == 400
    errors = res.json["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == expected_field
    assert expected_message in errors[0]["messages"][0]


@pytest.mark.parametrize(
    "license_value,expected_message",
    [
        (123, "Invalid license value provided"),
        (["cc-by-4.0"], "Invalid license value provided"),
    ],
)
def test_malformed_license(
    test_app, client_with_login, deposit_url, headers, license_value, expected_message
):
    """Test malformed license validation."""
    data = {
        "metadata": {
            "title": "Test",
            "upload_type": "dataset",
            "description": "Test description",
            "creators": [{"name": "Test User"}],
            "license": license_value,
        }
    }
    res = client_with_login.post(deposit_url, json=data, headers=headers)
    assert res.status_code == 400
    errors = res.json["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "metadata.license"
    assert expected_message in errors[0]["messages"][0]


@pytest.mark.parametrize("license_value", ["cc-by-4.0", {"id": "cc-by-4.0"}])
def test_valid_license(
    test_app, client_with_login, deposit_url, headers, license_value
):
    """Test valid license formats (string and dict with id)."""
    data = {
        "metadata": {
            "title": "Test",
            "upload_type": "dataset",
            "description": "Test description",
            "creators": [{"name": "Test User"}],
            "license": license_value,
        }
    }
    res = client_with_login.post(deposit_url, json=data, headers=headers)
    assert res.status_code == 201
