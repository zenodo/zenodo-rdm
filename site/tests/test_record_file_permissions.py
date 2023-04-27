# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test Zenodo legacy permissions."""

from io import BytesIO

from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records import RDMParent, RDMRecord


def create_record_w_file(client, record, headers):
    """Create record with a file."""
    # Create draft
    record["files"] = {"enabled": True}
    response = client.post("/records", json=record, headers=headers)
    assert response.status_code == 201
    recid = response.json["id"]

    # Attach a file to it
    response = client.post(
        f"/records/{recid}/draft/files", headers=headers, json=[{"key": "test.pdf"}]
    )
    assert response.status_code == 201
    response = client.put(
        f"/records/{recid}/draft/files/test.pdf/content",
        headers={
            "content-type": "application/octet-stream",
            "accept": "application/json",
        },
        data=BytesIO(b"testfile"),
    )
    assert response.status_code == 200
    response = client.post(
        f"/records/{recid}/draft/files/test.pdf/commit", headers=headers
    )
    assert response.status_code == 200

    # Publish it
    response = client.post(f"/records/{recid}/draft/actions/publish", headers=headers)
    assert response.status_code == 202

    return recid


def _add_to_community(record, community, service, db):
    """Add a record to a community."""
    record.parent.communities.add(community._record, default=False)
    record.parent.commit()
    record.commit()
    db.session.commit()
    service.indexer.index(record, arguments={"refresh": True})
    return record


def _add_permission_flags(value, record, db):
    db_record = RDMRecord.get_record(record._record.id)
    db_record.parent.permission_flags = {"can_community_read_files": value}
    db_record.parent.commit()
    db.session.commit()


def test_community_can_not_access_restricted_files(
    test_user,
    client,
    uploader,
    community_owner,
    headers,
    community,
    minimal_record,
    db,
):
    """Test the access to restricted files of a record for record owner, community owner, a simple user and anon (can_community_read_files flag is False)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(False, req_item, db)

    _add_to_community(req_item._record, community, service, db)
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner doesn't have access to file
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 403
    community_owner.logout(client)

    # random user doesn't have access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)

    # Anonymous user doesn't have access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_community_can_access_restricted_files(
    test_user,
    client,
    uploader,
    community_owner,
    headers,
    community,
    minimal_record,
    db,
):
    """Test the access to restricted files of a record for record owner, community owner, a simple user and anon (can_community_read_files flag is True)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(True, req_item, db)

    _add_to_community(req_item._record, community, service, db)
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner has access to file
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 200
    community_owner.logout(client)

    # random user doesn't have access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)

    # Anonymous user doesn't have access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_community_can_access_restricted_files_missing_flag(
    test_user,
    client,
    uploader,
    community_owner,
    headers,
    community,
    minimal_record,
    db,
):
    """Test the access to restricted files of a record for record owner, community owner, a simple user and anon (can_community_read_files flag is missing)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    db_record = RDMRecord.get_record(req_item._record.id)
    db_record.parent.permission_flags = {"can_do_something_else": True}
    db_record.parent.commit()
    db.session.commit()

    _add_to_community(req_item._record, community, service, db)
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner has access to file
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 200
    community_owner.logout(client)

    # random user doesn't have access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)

    # Anonymous user doesn't have access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_community_can_access_restricted_files_missing_field(
    test_user,
    client,
    uploader,
    community_owner,
    headers,
    community,
    minimal_record,
    db,
):
    """Test the access to restricted files of a record for record owner, community owner, a simple user and anon (permission_flags field is missing)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    _add_to_community(req_item._record, community, service, db)
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner has access to file
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 200
    community_owner.logout(client)

    # random user doesn't have access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)

    # Anonymous user doesn't have access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_everybody_can_access_public_files_flag_is_true(
    test_user,
    client,
    uploader,
    community_owner,
    headers,
    community,
    minimal_record,
    db,
):
    """Test the access to public files of a record for record owner, community owner and a simple user (can_community_access flag is True)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)

    # publish a record with public files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(True, req_item, db)

    _add_to_community(req_item._record, community, service, db)
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner has access to files
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 200
    community_owner.logout(client)

    # random user has access to files
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 200
    test_user.logout(client)


def test_everybody_can_access_public_files_flag_is_false(
    test_user,
    client,
    uploader,
    community_owner,
    headers,
    community,
    minimal_record,
    db,
):
    """Test the access to public files of a record for record owner, community owner and a simple user (can_community_access flag is False)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)

    # publish a record with public files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(False, req_item, db)

    _add_to_community(req_item._record, community, service, db)
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner has access to files
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 200
    community_owner.logout(client)

    # random user has access to files
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 200
    test_user.logout(client)


def test_only_owners_can_download_restricted_file(
    client,
    headers,
    minimal_record,
    uploader,
    test_user,
    community,
    db,
    community_owner,
):
    """Test that only record owner can download restricted files (can_community_access flag is False)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(False, req_item, db)

    url = f"/records/{recid}/files/test.pdf/content"

    # Owner can download file
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # Anonymous user can't download file
    response = client.get(url, headers=headers)
    assert response.status_code == 403

    # Different user can't download file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)

    # Community owner can't download file
    req_item = service.read(uploader.identity, recid)
    _add_to_community(req_item._record, community, service, db)
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 403
    community_owner.logout(client)


def test_communinty_can_download_restricted_file(
    client,
    headers,
    minimal_record,
    uploader,
    test_user,
    community,
    db,
    community_owner,
):
    """Test that only record owner can download restricted files (can_community_access flag is True)."""
    service = current_rdm_records_service
    record_owner = uploader.login(client)
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(True, req_item, db)

    url = f"/records/{recid}/files/test.pdf/content"

    # Owner can download file
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # Community owner can download file
    req_item = service.read(uploader.identity, recid)
    _add_to_community(req_item._record, community, service, db)
    comm_owner = community_owner.login(client)
    response = comm_owner.get(url, headers=headers)
    assert response.status_code == 200
    community_owner.logout(client)

    # Anonymous user can't download file
    response = client.get(url, headers=headers)
    assert response.status_code == 403

    # Different user can't download file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)


def test_everybody_can_download_public_files_flag_is_true(
    uploader,
    client,
    headers,
    community,
    minimal_record,
    db,
):
    """Test that any user can download non-restricted files (can_community_access flag is True)."""
    service = current_rdm_records_service

    # Create minimal record with public files
    record_owner = uploader.login(client)
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)
    uploader.logout(client)

    # add permission_flags
    _add_permission_flags(True, req_item, db)

    # Unauthenticated user can list files
    url = f"/records/{recid}/files"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json["entries"]

    # Check if we can download every file
    for file_entry in response.json["entries"]:
        file_key = file_entry["key"]
        resp = client.get(f"/records/{recid}/files/{file_key}/content", headers=headers)
        assert resp.status_code == 200


def test_everybody_can_download_public_files_flag_is_false(
    uploader,
    client,
    headers,
    community,
    minimal_record,
    db,
):
    """Test that any user can download non-restricted files (can_community_access flag is False)."""
    service = current_rdm_records_service

    # Create minimal record with public files
    record_owner = uploader.login(client)
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)
    uploader.logout(client)

    # add permission_flags
    _add_permission_flags(False, req_item, db)

    # Unauthenticated user can list files
    url = f"/records/{recid}/files"
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json["entries"]

    # Check if we can download every file
    for file_entry in response.json["entries"]:
        file_key = file_entry["key"]
        resp = client.get(f"/records/{recid}/files/{file_key}/content", headers=headers)
        assert resp.status_code == 200


def test_community_owner_is_record_owner_flag_false(
    test_user,
    client,
    uploader,
    headers,
    community_with_uploader_owner,
    minimal_record,
    db,
):
    """Test the access to restricted files of a record for record owner who is a community owner (can_community_read_files flag is False)."""
    service = current_rdm_records_service
    owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(False, req_item, db)

    _add_to_community(req_item._record, community_with_uploader_owner, service, db)
    url = f"/records/{recid}/files"

    # record/community owner has access to files
    response = owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)


def test_community_owner_is_record_owner_flag_true(
    test_user,
    client,
    uploader,
    headers,
    community_with_uploader_owner,
    minimal_record,
    db,
):
    """Test the access to restricted files of a record for record owner who is a community owner (can_community_read_files flag is True)."""
    service = current_rdm_records_service
    owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "restricted"
    recid = create_record_w_file(owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags(True, req_item, db)

    _add_to_community(req_item._record, community_with_uploader_owner, service, db)
    url = f"/records/{recid}/files"

    # record/community owner has access to files
    response = owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)
