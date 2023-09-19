# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test community transform for RDM migration."""
import dictdiffer
import pytest

from zenodo_rdm_migrator.transform.communities import (
    ZenodoCommunityEntry,
    ZenodoCommunityMemberEntry,
)


@pytest.fixture(scope="module")
def zenodo_community_data():
    """Full Zenodo community as a dictionary."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "id": "migrator",
        "id_user": 1,
        "title": "Migrator community",
        "description": "Migrator testing community",
        "page": "",
        "curation_policy": "",
        "last_record_accepted": "2000-01-01T00:00:00",
        "logo_ext": None,
        "ranking": 0,
        "fixed_points": 0,
        "deleted_at": None,
    }


@pytest.fixture(scope="module")
def expected_rdm_community():
    """Expected community in zenodo-rdm."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "version_id": 1,
        "slug": "migrator",
        "json": {
            "files": {"enabled": True},
            "access": {
                "visibility": "public",
                "member_policy": "open",
                "record_policy": "open",
            },
            "metadata": {
                "page": "",
                "title": "Migrator community",
                "curation_policy": "",
                "description": "Migrator testing community",
            },
        },
        "bucket_id": None,
        "deletion_status": "P",
    }


@pytest.fixture(scope="module")
def expected_rdm_community_member():
    """Expected community member in zenodo-rdm."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "json": {},
        "version_id": 1,
        "role": "owner",
        "visible": True,
        "active": True,
        "user_id": 1,
        "group_id": None,
        "request_id": None,
    }


def test_community_entry(zenodo_community_data, expected_rdm_community):
    """Test the transformation of a full Zenodo community."""
    result = ZenodoCommunityEntry().transform(zenodo_community_data)
    assert not list(dictdiffer.diff(result, expected_rdm_community))


def test_community_member(zenodo_community_data, expected_rdm_community_member):
    """Test the transformation of a Zenodo community into rdm members."""
    result = ZenodoCommunityMemberEntry().transform(zenodo_community_data)
    assert not list(dictdiffer.diff(result, expected_rdm_community_member))
    assert zenodo_community_data["id_user"] == result["user_id"]
