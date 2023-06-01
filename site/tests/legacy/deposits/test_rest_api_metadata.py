# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test deposit metadata (REST API)."""

import json

import dictdiffer


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
    assert res.json["hits"]["total"] == 0


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
    res = client.post(deposit_url, data=json.dumps(test_data), headers=headers)
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

    ignored_keys = set()

    # doi is returned as a top level key (and not inside metadata)
    # TODO: Verify behaviour and fix
    # assert data["doi"] == test_data["metadata"]["doi"]
    ignored_keys.add("doi")

    differences = list(
        dictdiffer.diff(data["metadata"], expected_record_metadata, ignore=ignored_keys)
    )

    assert not differences
