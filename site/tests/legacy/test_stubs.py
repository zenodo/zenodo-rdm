# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test stub REST API endpoints."""


def test_extra_formats(
    test_app,
    client,
):
    """Test extra formats stub endpoints."""
    mimetype = "application/custom+xml"
    deposit_url = "/api/deposit/depositions/1234/formats"
    record_url = "/api/records/1234/formats"

    # GET /api/deposit/depositions/{:id}/formats
    res = client.get(deposit_url, headers={"Accept": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Dummy content for "{mimetype}".'}

    res = client.get(deposit_url, query_string={"mimetype": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Dummy content for "{mimetype}".'}

    res = client.get(deposit_url)
    assert res.status_code == 400
    assert res.json == {"message": "Invalid extra format MIMEType.", "status": 400}

    # PUT /api/deposit/depositions/{:id}/formats
    res = client.put(deposit_url, headers={"Content-Type": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Extra format "{mimetype}" updated.'}

    # DELETE /api/deposit/depositions/{:id}/formats
    res = client.delete(deposit_url, headers={"Content-Type": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Extra format "{mimetype}" deleted.'}

    # OPTIONS /api/deposit/depositions/{:id}/formats
    res = client.options(deposit_url)
    assert res.status_code == 200
    assert res.json == []

    # GET /api/records/{:id}/formats
    res = client.get(record_url, headers={"Accept": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Dummy content for "{mimetype}".'}

    res = client.get(record_url, query_string={"mimetype": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Dummy content for "{mimetype}".'}

    res = client.get(record_url)
    assert res.status_code == 400
    assert res.json == {"message": "Invalid extra format MIMEType.", "status": 400}

    # OPTIONS /api/records/{:id}/formats
    res = client.options(record_url)
    assert res.status_code == 200
    assert res.json == []
