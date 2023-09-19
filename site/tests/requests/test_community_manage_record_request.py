# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test Zenodo community manage record request."""
import arrow
import pytest
from invenio_access.permissions import system_identity
from invenio_communities.generators import CommunityRoleNeed
from invenio_rdm_records.proxies import current_rdm_records
from invenio_rdm_records.records import RDMParent, RDMRecord
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_requests import current_requests_service

from zenodo_rdm.legacy.requests.utils import submit_community_manage_record_request


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


def _create_legacy_record(identity, record, permission_flags, db, service):
    """Create and publish a legacy record"""
    record["files"]["enabled"] = False
    draft = service.create(identity, record)
    record = service.publish(identity, draft.id)

    # modify record in the db
    db_record = RDMRecord.get_record(record._record.id)
    db_record.parent.permission_flags = permission_flags
    db_record.parent.commit()
    db.session.commit()

    service.indexer.index(db_record)
    db_record.index.refresh()

    return db_record


def _add_to_community(record, community, service, db):
    """Add a record to a community."""
    record.parent.communities.add(community._record, default=False)
    record.parent.commit()
    record.commit()
    db.session.commit()
    service.indexer.index(record, arguments={"refresh": True})
    return record


def _add_embargo(record, db):
    """Add embargo. Only for permission check purpose."""
    record.access.embargo.until = arrow.utcnow().shift(days=-10).datetime
    record.access.embargo.active = True
    record.commit()
    db.session.commit()


def test_submit_a_request(uploader):
    """Tests creation and submission of a community manage record request."""
    request_item = submit_community_manage_record_request(uploader.id)
    db_request = current_requests_service.read(
        system_identity, request_item._request.id
    )

    assert db_request["status"] == "submitted"
    assert db_request["type"] == "community-manage-record"
    assert db_request["receiver"] == {"user": "1"}
    assert db_request["topic"] is None
    assert db_request["created_by"] == {"user": "system"}
    assert db_request["title"] == "Communities manage legacy records"
    assert db_request["expires_at"] is not None
    assert db_request["description"].startswith(
        "<h4>Some of your records, that are going through the migration"
    )


def test_decline_a_request_no_communities(
    client,
    minimal_record,
    headers,
    uploader,
    db,
    service,
):
    """Tests case when record doesn't belong to any community."""
    record_owner = uploader.login(client)

    # publish a legacy record
    legacy_record = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )

    # create and submit a request
    request_item = submit_community_manage_record_request(uploader.id)
    request = request_item._request

    # decline a request
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert "declined" == response.json["status"]
    assert response.json["is_closed"] is True

    # check that the flag is removed from the record
    res_record = RDMRecord.get_record(legacy_record.id)
    assert res_record.parent.permission_flags == {}


def test_decline_a_request_no_legacy_records(
    client,
    minimal_record,
    headers,
    uploader,
    db,
    service,
):
    """Tests that if user doesn't have legacy records, the request will be declined."""
    record_owner = uploader.login(client)

    # publish a non-legacy record
    _ = _create_legacy_record(uploader.identity, minimal_record, {}, db, service)

    # create and submit a request
    request_item = submit_community_manage_record_request(uploader.id)
    request = request_item._request

    # decline a request
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert "declined" == response.json["status"]
    assert response.json["is_closed"] is True


def test_accept_a_request_no_legacy_records(
    client,
    minimal_record,
    headers,
    uploader,
    db,
    service,
):
    """Tests that if user doesn't have legacy records, the request will be accepted."""
    record_owner = uploader.login(client)

    # publish a non-legacy record
    _ = _create_legacy_record(uploader.identity, minimal_record, {}, db, service)

    # create and submit a request
    request_item = submit_community_manage_record_request(uploader.id)
    request = request_item._request

    # accept a request
    response = _send_post_action("accept", request.id, record_owner, headers, 200)
    assert "accepted" == response.json["status"]
    assert response.json["is_closed"] is True


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
    """Tests accept a community manage record request for different users."""
    record_owner = uploader.login(client)

    # create 2 legacy records (with permission flag)
    legacy_record1 = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )
    legacy_record2 = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )

    community_owner.identity.provides.add(CommunityRoleNeed(community.id, "owner"))
    _add_to_community(legacy_record1, community, service, db)

    # create and submit a request
    request_item = submit_community_manage_record_request(uploader.id)
    request = request_item._request

    # accept a request
    response = _send_post_action("accept", request.id, record_owner, headers, 200)
    assert "accepted" == response.json["status"]
    assert response.json["is_closed"] is True

    # check that the flag is removed from both records
    res_record1 = RDMRecord.get_record(legacy_record1.id)
    assert res_record1.parent.permission_flags == {}

    res_record2 = RDMRecord.get_record(legacy_record2.id)
    assert res_record2.parent.permission_flags == {}

    # check that comment was added
    response = record_owner.get(f"/requests/{request.id}/timeline", headers=headers)
    assert (
        response.json["hits"]["hits"][0]["payload"]["content"]
        == "You accepted the request. The community curators "
        "can now manage all of your legacy records."
    )

    # check permissions
    # tested on the lift embargo action, as editing a record is a bigger headache, while the
    # same permissions affects them
    recid = legacy_record1["id"]

    # record owner can lift embargo
    _add_embargo(res_record1, db)
    service.lift_embargo(_id=recid, identity=uploader.identity)

    # community owner can lift embargo
    _add_embargo(res_record1, db)
    service.lift_embargo(_id=recid, identity=community_owner.identity)

    # random user can't lift embargo
    _add_embargo(res_record1, db)
    with pytest.raises(PermissionDeniedError) as e:
        service.lift_embargo(_id=recid, identity=test_user.identity)


def test_decline_a_request(
    client,
    minimal_record,
    headers,
    uploader,
    test_user,
    service,
    db,
    community,
    community_owner,
    community_with_uploader_owner,
):
    """Tests decline a request for different users (with legacy records and 1 my community 1 not mine)."""
    record_owner = uploader.login(client)

    # create 2 legacy records (with permission flag)
    legacy_record1 = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )
    legacy_record2 = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )

    # add both records to someone else's community
    community_owner.identity.provides.add(CommunityRoleNeed(community.id, "owner"))
    _add_to_community(legacy_record1, community, service, db)
    _add_to_community(legacy_record2, community, service, db)

    # add both records to my community
    my_community_id = community_with_uploader_owner.id
    uploader.identity.provides.add(CommunityRoleNeed(my_community_id, "owner"))
    _add_to_community(legacy_record1, community_with_uploader_owner, service, db)
    _add_to_community(legacy_record2, community_with_uploader_owner, service, db)

    # create and submit a request
    request_item = submit_community_manage_record_request(uploader.id)
    request = request_item._request

    # decline a request
    response = _send_post_action("decline", request.id, record_owner, headers, 200)
    assert "declined" == response.json["status"]
    assert response.json["is_closed"] is True

    # check that the flag is removed from both records
    res_record1 = RDMRecord.get_record(legacy_record1.id)
    assert res_record1.parent.permission_flags == {}

    res_record2 = RDMRecord.get_record(legacy_record2.id)
    assert res_record2.parent.permission_flags == {}

    # check that records only have my communities left
    assert res_record1.parent["communities"] == {"ids": [my_community_id]}
    assert res_record2.parent["communities"] == {"ids": [my_community_id]}

    # check permissions
    # tested on the lift embargo action, as editing a record is a bigger headache, while the
    # same permissions affects them
    recid = legacy_record1["id"]

    # record owner can lift embargo
    _add_embargo(res_record1, db)
    service.lift_embargo(_id=recid, identity=uploader.identity)

    # community owner can't lift embargo
    _add_embargo(res_record1, db)
    with pytest.raises(PermissionDeniedError) as e:
        service.lift_embargo(_id=recid, identity=community_owner.identity)

    # random user can't lift embargo
    _add_embargo(res_record1, db)
    with pytest.raises(PermissionDeniedError) as e:
        service.lift_embargo(_id=recid, identity=test_user.identity)


def test_request_expire(
    client,
    minimal_record,
    headers,
    uploader,
    test_user,
    community,
    community_owner,
    service,
    db,
):
    """Tests expire a request for different users."""
    record_owner = uploader.login(client)

    # create 2 legacy records (with permission flag)
    legacy_record1 = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )
    legacy_record2 = _create_legacy_record(
        uploader.identity,
        minimal_record,
        {"can_community_manage_record": True},
        db,
        service,
    )

    community_owner.identity.provides.add(CommunityRoleNeed(community.id, "owner"))
    _add_to_community(legacy_record1, community, service, db)

    # create and submit a request
    request_item = submit_community_manage_record_request(uploader.id)
    request = request_item._request

    # expire a request
    result = current_requests_service.execute_action(
        system_identity, request.id, "expire"
    )
    assert result["status"] == "expired"
    assert result["is_closed"] is True

    # check that the flag is removed from both records
    res_record1 = RDMRecord.get_record(legacy_record1.id)
    assert res_record1.parent.permission_flags == {}

    res_record2 = RDMRecord.get_record(legacy_record2.id)
    assert res_record2.parent.permission_flags == {}

    # check that comment was added
    response = record_owner.get(f"/requests/{request.id}/timeline", headers=headers)
    assert (
        response.json["hits"]["hits"][0]["payload"]["content"]
        == "The request was expired. The community curators "
        "can now manage all of your legacy records."
    )

    # check permissions
    # tested on the lift embargo action, as editing a record is a bigger headache, while the
    # same permissions affects them
    recid = legacy_record1["id"]

    # record owner can lift embargo
    _add_embargo(res_record1, db)
    service.lift_embargo(_id=recid, identity=uploader.identity)

    # community owner can lift embargo
    _add_embargo(res_record1, db)
    service.lift_embargo(_id=recid, identity=community_owner.identity)

    # random user can't lift embargo
    _add_embargo(res_record1, db)
    with pytest.raises(PermissionDeniedError) as e:
        service.lift_embargo(_id=recid, identity=test_user.identity)
