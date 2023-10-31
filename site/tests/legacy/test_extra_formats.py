# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test extra formats legacy REST API endpoints."""

from io import BytesIO


def test_extra_formats(
    test_app,
    uploader,
    client,
    headers,
    deposit_url,
):
    """Test extra formats endpoints."""
    client = uploader.api_login(client)
    res = client.post(
        deposit_url,
        headers=headers,
        json={
            "metadata": {
                "title": "My first upload",
                "upload_type": "dataset",
                "description": "This is my first upload",
                "creators": [{"name": "Doe, John", "affiliation": "Zenodo"}],
            }
        },
    )
    assert res.status_code == 201
    data = res.json

    # Keep deposit info
    deposit_links = data["links"]

    # Upload a file
    res = client.post(
        deposit_links["files"],
        headers=headers,
        data={
            "name": "data.csv",
            "file": (BytesIO(b"1, 2, 3"), "data.csv"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 201

    # Publish deposit
    res = client.post(deposit_links["publish"], headers=headers)
    assert res.status_code == 202
    data = res.json

    record_link = data["links"]["record"]
    record_extra_formats_url = f"{record_link}/formats"
    deposit_link = deposit_links["self"]
    deposit_extra_formats_url = f"{deposit_link}/formats"

    mimetype = "application/custom+xml"

    for url in (deposit_extra_formats_url, record_extra_formats_url):
        res = client.get(url, headers={"Accept": mimetype})
        assert res.status_code == 404

        res = client.get(url, query_string={"mimetype": mimetype})
        assert res.status_code == 404

        res = client.get(url)
        assert res.status_code == 400
        assert res.json == {"message": "Invalid extra format MIMEType.", "status": 400}

        res = client.options(url)
        assert res.status_code == 200
        assert res.json == []

    # PUT /api/deposit/depositions/{:id}/formats
    res = client.put(
        deposit_extra_formats_url,
        data=BytesIO(b"custom xml"),
        headers={"Content-Type": mimetype},
    )
    assert res.status_code == 200
    assert res.json == {"message": f'Extra format "{mimetype}" updated.'}

    for url in (deposit_extra_formats_url, record_extra_formats_url):
        res = client.get(url, headers={"Accept": mimetype})
        assert res.status_code == 200
        assert res.data == b"custom xml"

        res = client.get(url, query_string={"mimetype": mimetype})
        assert res.status_code == 200
        assert res.data == b"custom xml"

        res = client.get(url)
        assert res.status_code == 400
        assert res.json == {"message": "Invalid extra format MIMEType.", "status": 400}

        res = client.options(url)
        assert res.status_code == 200
        data = res.json
        assert len(data) == 1
        assert data[0]["mimetype"] == "application/octet-stream"
        assert data[0]["checksum"] == "md5:e021897cee95295e216a1f911697bee9"
        assert data[0]["key"] == "application/custom+xml"
        assert data[0]["size"] == 10
        assert data[0]["status"] == "completed"
        assert data[0]["storage_class"] == "L"

    # DELETE /api/deposit/depositions/{:id}/formats
    res = client.delete(deposit_extra_formats_url, headers={"Content-Type": mimetype})
    assert res.status_code == 200
    assert res.json == {"message": f'Extra format "{mimetype}" deleted.'}

    for url in (deposit_extra_formats_url, record_extra_formats_url):
        res = client.get(url, headers={"Accept": mimetype})
        assert res.status_code == 404

        res = client.get(url, query_string={"mimetype": mimetype})
        assert res.status_code == 404

        res = client.get(url)
        assert res.status_code == 400
        assert res.json == {"message": "Invalid extra format MIMEType.", "status": 400}

        res = client.options(url)
        assert res.status_code == 200
        assert res.json == []
