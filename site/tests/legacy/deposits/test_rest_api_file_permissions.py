# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Legacy file permission regressions."""

from io import BytesIO


def _file(filename):
    """Build a file tuple accepted by Werkzeug test client."""
    return (BytesIO(filename.encode("utf8")), filename)


def _deposit_data():
    """Build minimal valid legacy deposit payload."""
    return {
        "metadata": {
            "upload_type": "dataset",
            "title": "Legacy file permission regression",
            "creators": [{"name": "Doe, John"}],
            "publication_date": "2020-01-01",
            "description": "Regression test",
            "access_right": "open",
        }
    }


def test_upload_after_published_files_read_does_not_forbid_next_upload(
    client, deposit_url, headers, uploader
):
    """Reading published files must not flip draft upload permissions globally."""
    client = uploader.api_login(client)

    res = client.post(deposit_url, json=_deposit_data(), headers=headers)
    assert res.status_code == 201, res.json
    first_links = res.json["links"]

    first_key = "first.txt"
    res = client.post(
        first_links["files"],
        data={"file": _file(first_key), "name": first_key},
    )
    assert res.status_code == 201, res.json

    # Bucket URL is needed to hit legacy /files/<bucket>/<key> on the published record.
    res = client.get(first_links["self"], headers=headers)
    assert res.status_code == 200, res.json
    bucket_url = res.json["links"]["bucket"]

    res = client.post(first_links["publish"])
    assert res.status_code == 202, res.json

    res = client.get(f"{bucket_url}/{first_key}", headers=headers)
    assert res.status_code == 200

    res = client.post(deposit_url, json=_deposit_data(), headers=headers)
    assert res.status_code == 201, res.json
    second_links = res.json["links"]

    second_key = "second.txt"
    res = client.post(
        second_links["files"],
        data={"file": _file(second_key), "name": second_key},
    )
    assert res.status_code == 201, res.json
