# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test Zenodo-RDM legacy deposit (REST API).

Tests were ported from: https://github.com/zenodo/zenodo/blob/master/tests/unit/deposit/test_api_simpleflow.py
"""

from io import BytesIO

import pytest
from flask import url_for
from invenio_search.api import current_search_client


def generate_file(filename, text=None):
    """Generate a file fixture."""
    content = text or filename.encode("utf8")
    return (BytesIO(content), filename)


def test_simple_rest_flow(test_app, client, deposit_url, headers, uploader):
    """Test simple flow using REST API."""
    test_data = dict(
        metadata=dict(
            upload_type="presentation",
            title="Test title",
            creators=[
                dict(name="Doe, John", affiliation="Atlantis"),
                dict(name="Smith, Jane", affiliation="Atlantis"),
            ],
            description="Test Description",
            publication_date="2013-05-08",
            access_right="open",
        )
    )

    # Try to create deposit as anonymous user (failing)
    with test_app.test_client() as unauth_client:
        response = unauth_client.post(deposit_url, json=test_data, headers=headers)
        assert response.status_code == 403

    client = uploader.api_login(client)

    # Create deposit
    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201
    data = response.json

    deposit_id = data["id"]
    links = data["links"]
    # Get deposition
    response = client.get(links["self"], headers=headers)
    assert response.status_code == 200

    # Upload 3 files
    filenames = []
    for i in range(3):
        name = f"test-{i}"
        file_name = f"{name}.txt"
        file = generate_file(file_name)
        response = client.post(links["files"], data={"file": file, "name": name})
        assert response.status_code == 201
        file_url = response.json["links"]["self"]
        filenames.append(file_name)

    # Publish deposition
    response = client.post(links["publish"])
    assert response.status_code == 202

    record_id = response.json["id"]

    # Check that same id is being used for both deposit and record.
    assert deposit_id == record_id

    # Does record exists?
    response = client.get(url_for("records.read", pid_value=record_id))

    assert response.status_code == 200

    # Second request will return forbidden since it's already published
    response = client.post(links["publish"])
    # TODO: Should be: 403
    assert response.status_code == 404, response.json

    # Not allowed to edit drafts
    response = client.put(links["self"], json=test_data, headers=headers)
    # TODO: Should be: 403
    assert response.status_code == 404, response.json

    # Not allowed to delete
    response = client.delete(links["self"], headers=headers)
    # TODO: Should be: 403
    assert response.status_code == 404, response.json

    # Not allowed to sort files
    response = client.get(links["files"], headers=headers)
    data = response.json
    assert response.status_code == 200, response.json

    files_list = [{"id": file_name} for file_name in filenames]
    files_list.reverse()
    response = client.put(links["files"], json=(files_list), headers=headers)
    # TODO: Should be: 403. It's a 405 because sorting is not yet implemented, e.g. the endpoint does not exist
    assert response.status_code == 405, response.json

    # Not allowed to add files
    response = client.post(
        links["files"],
        data={"file": generate_file("test-5.txt"), "name": "test-5.txt"},
    )
    assert response.status_code == 404, response.json

    # Not allowed to delete file
    response = client.delete(file_url, headers=headers)
    assert response.status_code == 403, response.json

    # Not allowed to rename file
    response = client.put(
        file_url,
        json=(dict(filename="another_test.pdf")),
        headers=headers,
    )
    # TODO: Should be: 403. File renaming is not yet implemented in Zenodo-RDM Legacy.
    assert response.status_code == 405, response.json


def test_simple_delete(test_app, client_with_login, deposit_url, headers, test_data):
    """Test deposit deletion."""
    client = client_with_login

    # Create a draft
    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json

    links = response.json["links"]

    # Check list
    # Refresh indices to have search updated
    current_search_client.indices.refresh()

    response = client.get(deposit_url, headers=headers)
    assert response.status_code == 200, response.json
    assert len(response.json) == 1

    # Delete
    response = client.delete(links["self"])
    assert response.status_code == 204, response.json

    # Check list
    response = client.get(deposit_url, headers=headers)
    assert response.status_code == 200, response.json
    assert len(response.json) == 0

    # Delete again
    response = client.delete(links["self"])
    # TODO: Should be: 410
    assert response.status_code == 404, response.json


def test_read_deposit_users(
    test_app, client, headers, deposit_url, test_data, test_user, uploader, superuser
):
    """Test read deposit by users."""
    owner = uploader
    not_owner = test_user

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]

    owner.api_logout(client)

    # Try anonymous user
    res = client.get(deposit_url, headers=headers)
    # TODO: Should be: 401
    assert res.status_code == 403, res.json

    # Try other user
    client = not_owner.api_login(client)
    res = client.get(deposit_url, headers=headers)
    assert res.status_code == 403
    not_owner.api_logout(client)

    # Try superuser user
    # TODO: in legacy zenodo it was admin. However admin does not have permissions (in tests, at least).
    # client = superuser.api_login(client)
    # res = client.get(deposit_url, headers=headers)
    # superuser.api_logout(client)

    # assert res.status_code == 200


def test_update_deposits_owner(
    test_app,
    client,
    headers,
    deposit_url,
    test_data,
    uploader,
):
    """Test update deposit by owner."""
    owner = uploader

    # Update 'title' metadata
    new_title = "A new title"
    update_metadata = {"metadata": {"title": new_title}}

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]

    # Try owner
    res = client.put(deposit_url, json=update_metadata, headers=headers)
    assert res.status_code == 200, res.json
    assert res.json["metadata"]["title"] == new_title


def test_update_deposit_not_owner(
    test_app,
    client,
    headers,
    deposit_url,
    test_data,
    uploader,
    test_user,
):
    """Test update deposit by not owner."""
    owner = uploader
    not_owner = test_user

    # Update 'title' metadata
    new_title = "A new title"
    update_metadata = {"metadata": {"title": new_title}}

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]
    owner.api_logout(client)

    # Try to udpate a draft with another user

    client = not_owner.api_login(client)
    res = client.put(deposit_url, json=update_metadata, headers=headers)
    assert res.status_code == 403


def test_update_deposit_anonymous(
    test_app,
    client,
    headers,
    deposit_url,
    test_data,
    uploader,
):
    """Test update deposit by not owner."""
    owner = uploader

    # Update 'title' metadata
    new_title = "A new title"
    update_metadata = {"metadata": {"title": new_title}}

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]
    client = owner.api_logout(client)

    # Try to udpate a draft with anonymous user
    res = client.put(deposit_url, json=update_metadata, headers=headers)
    # TODO: Should be: 401
    assert res.status_code == 403


def test_update_deposit_superuser(
    test_app,
    client,
    headers,
    deposit_url,
    test_data,
    uploader,
    superuser,
):
    """Test update deposit by superuser."""
    owner = uploader

    # Update 'title' metadata
    new_title = "A new title"
    update_metadata = {"metadata": {"title": new_title}}

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]
    owner.api_logout(client)

    # Try to udpate a draft with a super user
    client = superuser.api_login(client)
    res = client.put(deposit_url, json=update_metadata, headers=headers)
    assert res.status_code == 200


def test_delete_deposits_owner(
    test_app,
    client,
    headers,
    deposit_url,
    test_data,
    uploader,
):
    """Test read deposit by users."""
    owner = uploader

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]

    # Delete the draft
    res = client.delete(
        deposit_url,
        headers=headers,
    )

    assert res.status_code == 204, res.json


def test_delete_deposits_not_owner(
    test_app, client, headers, deposit_url, test_data, uploader, test_user
):
    """Test read deposit by users."""
    owner = uploader
    not_owner = test_user

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]

    owner.api_logout(client)

    # Delete the draft
    client = not_owner.api_login(client)
    res = client.delete(
        deposit_url,
        headers=headers,
    )

    assert res.status_code == 403, res.json


def test_delete_deposits_anonymous(
    test_app, client, headers, deposit_url, test_data, uploader, test_user
):
    """Test read deposit by users."""
    owner = uploader
    not_owner = test_user

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]

    owner.api_logout(client)

    # Delete the draft
    res = client.delete(
        deposit_url,
        headers=headers,
    )

    # TODO: Should be: 401
    assert res.status_code == 403, res.json


def test_delete_deposits_superuser(
    test_app, client, headers, deposit_url, test_data, uploader, superuser
):
    """Test read deposit by users."""
    owner = uploader

    # Create a draft using the owner user
    client = owner.api_login(client)

    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json
    deposit_url = response.json["links"]["self"]

    owner.api_logout(client)

    # Delete the draft
    client = superuser.api_login(client)
    res = client.delete(
        deposit_url,
        headers=headers,
    )

    assert res.status_code == 204, res.json


@pytest.mark.skip(reason="Works in other tests, so must be a test isolation issue.")
def test_versioning_rest_flow(
    test_app,
    db,
    deposit_url,
    client_with_login,
    headers,
):
    client = client_with_login
    test_data = dict(
        metadata=dict(
            upload_type="presentation",
            title="Test title",
            creators=[
                dict(name="Doe, John", affiliation="Atlantis"),
                dict(name="Smith, Jane", affiliation="Atlantis"),
            ],
            description="Test Description",
            publication_date="2013-05-08",
            access_right="open",
        )
    )

    # Create deposit
    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json

    data = response.json
    links = data["links"]

    # Get deposition
    response = client.get(links["self"], headers=headers)
    assert response.status_code == 200, response.json

    # Upload a file
    response = client.post(
        links["files"],
        data={
            "file": generate_file("test-1.txt"),
            "name": "test-1.txt",
        },
    )
    assert response.status_code == 201, response.json

    # Publish deposition
    response = client.post(links["publish"], headers=headers)
    assert response.status_code == 202, response.json

    # New version possible for published deposit
    response = client.post(response.json["links"]["newversion"], headers=headers)
    assert response.status_code == 201, response.json

    # Get the new version deposit
    new_draft_id = response.json["id"]
    new_draft_url = f"{deposit_url}/{new_draft_id}"
    response = client.get(new_draft_url, headers=headers)
    assert response.status_code == 200, response.json

    data = response.json
    links = data["links"]
    assert "latest_draft" in links
    new_deposit_url = links["self"]
    publish_endpoint = links["publish"]
    files_endpoint = links["files"]

    # Check that the file was copied over
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "test-1.txt"

    # Adding files allowed for new version
    file_name = "test-2.txt"
    response = client.post(
        files_endpoint,
        data={
            "file": generate_file("test-2.txt"),
            "name": file_name,
        },
    )
    assert response.status_code == 201, response.json

    # Delete the old file
    file_url = response.json["links"]["self"]
    response = client.delete(file_url, headers=headers)
    assert response.status_code == 204, response.json

    # Add required metadata for new version, this is a RDM specific flow.
    # publication_date is missing from the new version an a PUT expects all the new metadata.
    response = client.put(new_deposit_url, json=test_data, headers=headers)
    assert response.status_code == 200, response.json

    # TODO: Fixed when https://github.com/inveniosoftware/pytest-invenio/pull/104 is merged
    # Publish new version
    # response = client.post(publish_endpoint, headers=headers)
    # assert response.status_code == 202, response.json


def test_versioning_unpublished_fail(
    test_app, client_with_login, deposit_url, test_data, headers
):
    """Tests cannot create new version for unpublished record."""
    client = client_with_login
    test_data = dict(
        metadata=dict(
            upload_type="presentation",
            title="Test title",
            creators=[
                dict(name="Doe, John", affiliation="Atlantis"),
                dict(name="Smith, Jane", affiliation="Atlantis"),
            ],
            description="Test Description",
            publication_date="2013-05-08",
            access_right="open",
        )
    )

    # Create deposit
    response = client.post(deposit_url, json=test_data, headers=headers)
    assert response.status_code == 201, response.json

    # Versions links should only be returned for published records
    assert "versions" not in response.json["links"]

    # Try to manually create the version
    deposit_id = response.json["id"]
    response = client.post(f"/api/records/{deposit_id}/versions", headers=headers)

    # TODO: It should be: 403
    assert response.status_code == 404, response.json
