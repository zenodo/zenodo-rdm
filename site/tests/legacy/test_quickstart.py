# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test legacy API quickstart."""

from __future__ import absolute_import, print_function, unicode_literals

from io import BytesIO


def test_quickstart_workflow(
    test_app,
    test_user,
    client,
    headers,
    files_headers,
    deposit_url,
):
    """Test quickstart workflow."""
    # Try get deposits as anonymous user
    res = client.get(deposit_url)
    # TODO: Should be:
    # assert res.status_code == 401
    assert res.status_code == 403

    # Try get deposits as logged-in user
    client = test_user.api_login(client)
    res = client.get(deposit_url, headers=headers)
    assert res.status_code == 200
    assert res.json == []

    # Create a new deposit
    res = client.post(
        deposit_url,
        headers=headers,
        json={},
    )
    assert res.status_code == 201
    data = res.json
    assert data["title"] == ""
    assert "created" in data
    assert "modified" in data
    assert isinstance(data["id"], int)
    assert isinstance(data["record_id"], int)
    assert data["conceptrecid"]
    assert "metadata" in data
    assert "doi" not in data
    assert data["metadata"]["prereserve_doi"] == {
        "doi": f"10.5281/zenodo.{data['id']}",
        "recid": data["id"],
    }
    assert data["state"] == "unsubmitted"
    assert data["owner"] == int(test_user.id)

    # Keep deposit info
    deposit_links = data["links"]

    # Upload a file
    res = client.post(
        deposit_links["files"],
        headers=headers,
        data={
            "name": "my_first_file.csv",
            "file": (BytesIO(b"1, 2, 3"), "my_first_file.csv"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    data = res.json

    assert data["id"]  # file ID
    assert data["checksum"] == "66ce05ea43c73b8e33c74c12d0371bc9"
    assert data["filename"] == "my_first_file.csv"
    assert data["filesize"] == 7
    assert {"self", "download"} <= data["links"].keys()

    # Get and verify the file info
    res = client.get(data["links"]["self"])
    data = res.json
    assert res.status_code == 200
    assert data["id"]  # file ID
    assert data["checksum"] == "66ce05ea43c73b8e33c74c12d0371bc9"
    assert data["filename"] == "my_first_file.csv"
    assert data["filesize"] == 7
    assert {"self", "download"} <= data["links"].keys()

    # Upload another file, without the "name" parameter
    res = client.post(
        deposit_links["files"],
        headers=headers,
        data={
            # "name": "my_second_file.csv",
            "file": (BytesIO(b"1, 2, 3"), "my_second_file.csv"),
        },
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    data = res.json

    assert data["id"]  # file ID
    assert data["checksum"] == "66ce05ea43c73b8e33c74c12d0371bc9"
    assert data["filename"] == "my_second_file.csv"
    assert data["filesize"] == 7
    assert {"self", "download"} <= data["links"].keys()

    # Upload a file with /api/files
    bucket_url = deposit_links["bucket"]
    res = client.put(
        f"{bucket_url}/my_third_file.csv",
        headers=files_headers,
        data=BytesIO(b"4, 5, 6"),
    )
    assert res.status_code == 201
    data = res.json
    assert {"created", "updated"} <= data.keys()
    assert data["version_id"]
    assert data["mimetype"] == "text/csv"
    assert data["checksum"] == "md5:c2d626f8beba73ad0cf4e66214f7d949"
    assert data["key"] == "my_third_file.csv"
    assert data["size"] == 7
    assert data["is_head"] is True
    assert data["delete_marker"] is False
    assert {"self", "uploads", "version"} <= data["links"].keys()

    # modify deposit
    deposit = {
        "metadata": {
            "title": "My first upload",
            "upload_type": "dataset",
            "description": "This is my first upload",
            "creators": [{"name": "Doe, John", "affiliation": "Zenodo"}],
        }
    }
    res = client.put(
        deposit_links["self"],
        headers=headers,
        json=deposit,
    )
    assert res.status_code == 200

    # Publish deposit
    res = client.post(
        deposit_links["publish"],
        headers=headers,
    )
    assert res.status_code == 202
    data = res.json
    record_id = data["id"]
    record_links = data["links"]

    # Check that record exists.
    res = client.get(record_links["self"])
    assert res.status_code == 200
    data = res.json

    # Assert that a DOI has been assigned.
    # TODO: Shoule be:
    assert data["doi"] == f"10.5281/zenodo.{record_id}"
    # assert data["pids"]["doi"]["identifier"] == f"10.5281/zenodo.{record_id}"
