# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test legacy API quickstart."""

from __future__ import absolute_import, print_function, unicode_literals

from io import BytesIO


def test_autoaccept_owned_communities(
    test_app,
    uploader,
    community_with_uploader_owner,
    client,
    headers,
    deposit_url,
):
    """Automatically accept records requested by community owners."""
    community = community_with_uploader_owner
    client = uploader.login(client)

    # Create a new deposit
    res = client.post(
        deposit_url,
        headers=headers,
        json={
            "metadata": {
                "title": "My first upload",
                "upload_type": "dataset",
                "description": "This is my first upload",
                "creators": [{"name": "Doe, John", "affiliation": "Zenodo"}],
                "communities": [{"identifier": community["slug"]}],
            }
        },
    )
    assert res.status_code == 201
    assert res.json["metadata"]["communities"] == [
        {"identifier": community["slug"]},
    ]
    deposit_links = res.json["links"]

    # Upload a file
    files = {
        "file": (BytesIO(b"1, 2, 3"), "myfirstfile.csv"),
        "name": "myfirstfile.csv",
    }
    res = client.post(
        deposit_links["files"],
        headers=headers,
        data=files,
        content_type="multipart/form-data",
    )
    assert res.status_code == 201

    # Publish deposit
    res = client.post(
        deposit_links["publish"],
        headers=headers,
    )
    assert res.status_code == 202
    data = res.json
    record_links = data["links"]

    # Check that the record has been auto-accepted in the community
    res = client.get(record_links["self"])
    assert res.status_code == 200
    data = res.json
    assert data["parent"]["communities"]["ids"] == [community["id"]]

    # Cehck that the custom field has been cleared
    assert "legacy:communities" not in data.get("custom_fields", {})
