# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-01-01 12:00:00.00000N.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test featured community transform for RDM migration."""
import dictdiffer
import pytest

from zenodo_rdm_migrator.transform.entries.communities import (
    ZenodoFeaturedCommunityEntry,
)


@pytest.fixture(scope="module")
def zenodo_featured_community_data():
    """Full Zenodo featured community as a dictionary."""
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
        "is_featured": True,
        "featured_created": "2023-01-01 12:00:00.00000",
        "featured_updated": "2023-01-01 12:00:00.00000",
        "featured_start_date": "2023-01-01 12:00:00.00000",
    }


@pytest.fixture(scope="module")
def zenodo_non_featured_community_data():
    """Full Zenodo non-featured community as a dictionary."""
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
        "is_featured": False,
    }


@pytest.fixture(scope="module")
def expected_rdm_featured_community():
    """Expected featured community in zenodo-rdm. Community id is programatically added when loading."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-01 12:00:00.00000",
        "start_date": "2023-01-01 12:00:00.00000",
    }


def test_featured_community_entry(
    zenodo_featured_community_data, expected_rdm_featured_community
):
    """Test the transformation of a featured community.
    the community id is added when the community table is generated. Thus, it is not in the transformation result.
    """
    result = ZenodoFeaturedCommunityEntry().transform(zenodo_featured_community_data)
    assert not list(dictdiffer.diff(result, expected_rdm_featured_community))


def test_non_featured_community_transform(zenodo_non_featured_community_data):
    """Test the transformation of a non featured community.

    This test should fail because the community is not featured, therefore it has fields missing (e.g. featured_start_date).
    """
    with pytest.raises(KeyError):
        ZenodoFeaturedCommunityEntry().transform(zenodo_non_featured_community_data)
