# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test Zenodo legacy record upgrade request."""
from io import BytesIO

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.records import RDMParent, RDMRecord
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_requests import current_requests_service

from zenodo_rdm.legacy.requests.utils import submit_record_upgrade_request


@pytest.fixture()
def service(running_app):
    """The record service."""
    return current_rdm_records.records_service


def _send_post_action(action, request_id, client, headers, expected_status_code):
    """Send http-post request to perform an action on a request"""
    response = client.post(
        f"/requests/{request_id}/actions/{action}",
        headers=headers,
        json={},
    )

    assert response.status_code == expected_status_code
    return response


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


def _add_permission_flags(permission_flags, record, db):
    db_record = RDMRecord.get_record(record._record.id)
    db_record.parent.permission_flags = permission_flags
    db_record.parent.commit()
    db.session.commit()


def _create_legacy_record(identity, record, permission_flags, db, service):
    """Create and publish a legacy record"""
    draft = service.create(identity, record)
    record = service.publish(identity, draft.id)

    # modify record in the db
    db_record = RDMRecord.get_record(record._record.id)
    db_record.parent.permission_flags = permission_flags
    db_record.parent.commit()
    db.session.commit()

    return db_record


def _add_to_community(record, community, service, db):
    """Add a record to a community."""
    record.parent.communities.add(community._record, default=False)
    record.parent.commit()
    record.commit()
    db.session.commit()
    service.indexer.index(record, arguments={"refresh": True})
    return record


def test_submit_a_request(
    client,
    minimal_record,
    uploader,
    service,
    db,
    community,
    headers,
    community_owner,
    test_user,
):
    """Tests creation and submission of a legacy record upgrade request."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)

    request_item = submit_record_upgrade_request(legacy_record)
    db_request = current_requests_service.read(
        system_identity, request_item._request.id
    )

    recid = legacy_record["id"]
    assert db_request["status"] == "submitted"
    assert db_request["type"] == "legacy-record-upgrade"
    assert db_request["receiver"] == {"user": "1"}
    assert db_request["topic"] == {"record": f"{recid}"}
    assert db_request["created_by"] == {"user": "system"}
    assert db_request["title"] == "Upgrade your legacy record: A Romans story"
    assert db_request["expires_at"] is not None
    assert db_request["description"].startswith(
        "The current record uses legacy behavior which has been removed from"
    )

    # check permissions
    recid = legacy_record["id"]
    url = f"/records/{recid}/files"

    # record owner has access to files
    response = record_owner.get(url, headers=headers)
    assert response.status_code == 200
    uploader.logout(client)

    # community owner doesn't have access to files
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


def test_record_is_not_migrated(client, minimal_record, uploader, service, db, headers):
    """Tests that legacy record upgrade request can't be created for non-migrated records."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags without 'can_community_read_files'
    _add_permission_flags({}, req_item, db)

    legacy_record = req_item._record

    with pytest.raises(Exception) as e:
        submit_record_upgrade_request(legacy_record)

    assert (
        str(e.value)
        == "Legacy record upgrade request can't be created. The record is not a migrated one."
    )

    # without 'permission_flags'
    legacy_record.parent.pop("permission_flags")
    legacy_record.parent.commit()
    db.session.commit()

    with pytest.raises(Exception) as e:
        submit_record_upgrade_request(legacy_record)

    assert (
        str(e.value)
        == "Legacy record upgrade request can't be created. The record is not a migrated one."
    )


def test_request_already_exists(
    client, minimal_record, uploader, service, db, community, headers
):
    """Tests that error raises in case a duplicate request is being created."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    assert request_item._request["status"] == "submitted"

    with pytest.raises(Exception) as e:
        submit_record_upgrade_request(legacy_record)

    assert (
        str(e.value)
        == "There is already an open legacy record upgrade request for this record."
    )


def test_submit_record_with_public_files(
    client, minimal_record, uploader, service, db, headers
):
    """Tests that error raises in case request is being created for record with public files."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    minimal_record["access"]["files"] = "public"
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    with pytest.raises(Exception) as e:
        submit_record_upgrade_request(req_item._record)

    assert (
        str(e.value)
        == "Legacy record upgrade request can't be created. The record doesn't have restricted files."
    )


def test_submit_record_with_0_communitites(
    client, minimal_record, uploader, service, db, headers
):
    """Tests that error raises in case request is being created for record without communities."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    with pytest.raises(Exception) as e:
        submit_record_upgrade_request(req_item._record)

    assert (
        str(e.value)
        == "Legacy record upgrade request can't be created. The record doesn't belong to any community."
    )


def test_accept_a_request(
    client,
    minimal_record,
    headers,
    uploader,
    test_user,
    service,
    db,
    community,
    community_owner,
):
    """Tests accept a legacy record upgrade request for different users."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # create and submit a request
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    uploader.logout(client)

    # anonymous user can't accept the request
    _send_post_action("accept", request.id, client, headers, 403)

    # random authorized user can't accept the request
    simple_user = test_user.login(client)
    _send_post_action("accept", request.id, simple_user, headers, 403)
    test_user.logout(client)

    # accept a request as a record owner
    record_owner = uploader.login(client)
    response = _send_post_action("accept", request.id, record_owner, headers, 200)
    assert "accepted" == response.json["status"]
    assert response.json["is_closed"] is True

    # check that the flag is removed from db
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}

    # check that comment was added
    response = record_owner.get(f"/requests/{request.id}/timeline", headers=headers)
    assert (
        response.json["hits"]["hits"][0]["payload"]["content"]
        == "You accepted the request. The record is now upgraded "
        "and all the communities that this record belongs to will"
        " now have access to the restricted files."
    )

    # check permissions
    recid = legacy_record["id"]
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

    # random user doesn't have access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 403
    test_user.logout(client)

    # Anonymous user doesn't have access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 403


def test_accept_a_request_no_flag(
    client, minimal_record, headers, uploader, service, db, community
):
    """Tests that if flag is absent, the request will be accepted."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # create and submit a request
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # remove flag
    legacy_record.parent.permission_flags = {}
    legacy_record.parent.commit()
    db.session.commit()

    # accept a request
    response = _send_post_action("accept", request.id, record_owner, headers, 200)
    assert "accepted" == response.json["status"]
    assert response.json["is_closed"] is True


def test_accept_a_request_no_field(
    client, minimal_record, headers, uploader, service, db, community
):
    """Tests that if permission_flags field is absent, the request will be accepted."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # create and submit a request
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # remove the whole field
    legacy_record.parent.pop("permission_flags")
    legacy_record.parent.commit()
    db.session.commit()

    # accept a request
    response = _send_post_action("accept", request.id, record_owner, headers, 200)
    assert "accepted" == response.json["status"]
    assert response.json["is_closed"] is True


def test_decline_a_request(
    client,
    minimal_record,
    headers,
    uploader,
    test_user,
    community,
    community2,
    service,
    db,
    community_owner,
):
    """Tests decline a legacy record upgrade request for different users (restricted files and present communities)."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # add to multiple communities
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    _add_to_community(legacy_record, community2, service, db)

    # create and submit a request
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    uploader.logout(client)

    # anonymous user can't decline the request
    _send_post_action("decline", request.id, client, headers, 403)

    # random authorized user can't decline the request
    simple_user = test_user.login(client)
    _send_post_action("decline", request.id, simple_user, headers, 403)
    test_user.logout(client)

    # decline a request successfully as a record owner
    record_owner = uploader.login(client)
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert response.json["status"] == "declined"
    assert response.json["is_closed"] is True

    # check that the flag is removed from db and record has no communities
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}
    assert res_record.parent.communities.ids == []

    # check that no comment was added
    response = record_owner.get(
        f"/requests/{request.id}/timeline",
        headers=headers,
    )
    assert response.json["hits"]["hits"] == []

    # check permissions
    recid = legacy_record["id"]
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


def test_decline_a_request_no_flag(
    client, minimal_record, headers, uploader, community, service, db
):
    """Tests decline a legacy record upgrade request for a record without can_community_access flag."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # add to community
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)

    # create and submit a request
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # remove flag
    legacy_record.parent.permission_flags = {}
    legacy_record.parent.commit()
    db.session.commit()

    # decline a request
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert response.json["status"] == "declined"
    assert response.json["is_closed"] is True

    # check that the record was removed from a community
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.communities.ids == []


def test_decline_a_request_no_communities(
    client,
    minimal_record,
    headers,
    uploader,
    service,
    db,
    community,
    community_owner,
    test_user,
):
    """Tests decline a legacy record upgrade request for a record with 0 communities and restricted files."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # create and submit a request
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # remove community from record
    legacy_record.parent.communities.remove(community._record)
    legacy_record.parent.commit()
    db.session.commit()
    service.indexer.index(legacy_record, arguments={"refresh": True})

    assert legacy_record.parent.communities.ids == []

    # decline a request
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert response.json["status"] == "declined"
    assert response.json["is_closed"] is True

    # check that the flag is removed from db
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}

    # check that comment was added
    response = record_owner.get(f"/requests/{request.id}/timeline", headers=headers)
    assert response.json["hits"]["hits"][1]["payload"]["event"] == "declined"
    assert (
        response.json["hits"]["hits"][0]["payload"]["content"]
        == "As a result of decline action record was not removed from its communities because it doesn't belong to any."
    )

    # check permissions
    recid = legacy_record["id"]
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


def test_decline_a_request_public_files(
    client,
    minimal_record,
    headers,
    uploader,
    service,
    db,
    community,
    community_owner,
    test_user,
):
    """Tests decline a legacy record upgrade request for a record with public files and present community."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # add to community
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)

    # create and submit a request
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # unrestrict files
    legacy_record.access.protection.files = "public"
    legacy_record.commit()
    db.session.commit()

    # decline a request
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert response.json["status"] == "declined"
    assert response.json["is_closed"] is True

    # check that the flag is removed from db
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}

    # check that record was not removed from a community
    assert res_record.parent.communities.ids[0] == community.id

    # check that comment was added
    response = record_owner.get(f"/requests/{request.id}/timeline", headers=headers)
    assert response.json["hits"]["hits"][1]["payload"]["event"] == "declined"
    assert (
        response.json["hits"]["hits"][0]["payload"]["content"]
        == "As a result of decline action record was not removed from its communities because it doesn't have restricted files."
    )

    # check permissions
    recid = legacy_record["id"]
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

    # random user has access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 200
    test_user.logout(client)

    # Anonymous user has access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 200


def test_request_expire(
    client,
    minimal_record,
    headers,
    uploader,
    test_user,
    community,
    community2,
    service,
    db,
    community_owner,
):
    """Tests expire a legacy record upgrade request for different users (restricted files and present communities)."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # add to multiple communities
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    _add_to_community(legacy_record, community2, service, db)

    # create and submit a request
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # record owner can't expire the request
    with pytest.raises(PermissionDeniedError):
        current_requests_service.execute_action(uploader.identity, request.id, "expire")
    uploader.logout(client)

    # random authorized user can't expire the request
    test_user.login(client)
    with pytest.raises(PermissionDeniedError):
        current_requests_service.execute_action(
            test_user.identity, request.id, "expire"
        )
    test_user.logout(client)

    # expire a request successfully as a system process
    result = current_requests_service.execute_action(
        system_identity, request.id, "expire"
    )
    assert result["status"] == "expired"
    assert result["is_closed"] is True

    # check that the flag is removed from db and record has no communities
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}
    assert res_record.parent.communities.ids == []

    # check permissions
    recid = legacy_record["id"]
    url = f"/records/{recid}/files"

    # record owner has access to files
    record_owner = uploader.login(client)
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


def test_expire_a_request_no_communities(
    client,
    minimal_record,
    headers,
    uploader,
    service,
    db,
    community,
    community_owner,
    test_user,
):
    """Tests expire a legacy record upgrade request for a record with 0 communities."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # create and submit a request
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # remove community from record
    legacy_record.parent.communities.remove(community._record)
    legacy_record.parent.commit()
    db.session.commit()
    service.indexer.index(legacy_record, arguments={"refresh": True})

    assert legacy_record.parent.communities.ids == []

    # expire a request
    result = current_requests_service.execute_action(
        system_identity, request.id, "expire"
    )
    assert result["status"] == "expired"
    assert result["is_closed"] is True

    # check that the flag is removed from db
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}

    # check permissions
    recid = legacy_record["id"]
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


def test_expire_a_request_public_files(
    client,
    minimal_record,
    headers,
    uploader,
    service,
    db,
    community,
    community_owner,
    test_user,
):
    """Tests expire a legacy record upgrade request for a record with public files and a community."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # add to community
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)

    # create and submit a request
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # unrestrict files
    legacy_record.access.protection.files = "public"
    legacy_record.commit()
    db.session.commit()

    # expire a request
    result = current_requests_service.execute_action(
        system_identity, request.id, "expire"
    )
    assert result["status"] == "expired"
    assert result["is_closed"] is True

    # check that the flag is removed from db
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}

    # check that record was not removed from a community
    assert res_record.parent.communities.ids[0] == community.id

    # check permissions
    recid = legacy_record["id"]
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

    # random user has access to file
    simple_user = test_user.login(client)
    response = simple_user.get(url, headers=headers)
    assert response.status_code == 200
    test_user.logout(client)

    # Anonymous user has access to file
    response = client.get(url, headers=headers)
    assert response.status_code == 200


def test_expire_a_request_no_flag(
    client, minimal_record, headers, uploader, service, db, community
):
    """Tests expire a legacy record upgrade request for a record without can_community_access flag."""
    record_owner = uploader.login(client)

    # publish a record with restricted files
    recid = create_record_w_file(record_owner, minimal_record, headers)
    req_item = service.read(uploader.identity, recid)

    # add permission_flags
    _add_permission_flags({"can_community_read_files": False}, req_item, db)

    # create and submit a request
    legacy_record = req_item._record
    _add_to_community(legacy_record, community, service, db)
    request_item = submit_record_upgrade_request(legacy_record)
    request = request_item._request

    # remove flag
    legacy_record.parent.permission_flags = {}
    legacy_record.parent.commit()
    db.session.commit()

    # expire a request
    result = current_requests_service.execute_action(
        system_identity, request.id, "expire"
    )
    assert result["status"] == "expired"
    assert result["is_closed"] is True
