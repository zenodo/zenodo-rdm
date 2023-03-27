# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test record transform for RDM migration."""

from datetime import datetime
from unittest.mock import patch

import dictdiffer
import pytest

from zenodo_rdm.migrator.transform.requests import ZenodoRequestTransform


@pytest.fixture(scope="module")
def zenodo_request_data():
    """Extracted Zenodo request as a dictionary."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "id_community": "comm",
        "recid": "123456",
        "title": "Test title",
        "owners": "3",
    }


@pytest.fixture(scope="module")
def expected_rdm_request_entry():
    """Expected request entry for RDM."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "version_id": 1,
        "json": {
            "type": "community-inclusion",
            "title": "Test title",
            "topic": {"record": "123456"},
            "status": "submitted",
            "receiver": {"community": "comm"},
            "created_by": {"user": "3"},
            "$schema": "local://requests/request-v1.0.0.json",
        },
        "expires_at": "2024-01-01T12:00:00",
        "number": None,
    }


class MockDatetime:
    """Mocked datetime."""

    def today(self):
        """returns constant datetime."""
        return datetime(2023, 1, 1, 12, 00, 00, 00000)


@patch("zenodo_rdm.migrator.transform.requests.datetime", MockDatetime())
def test_zenodo_request_transform(zenodo_request_data, expected_rdm_request_entry):
    """Test the transformation of a request into a request and a relation."""
    result = ZenodoRequestTransform()._transform(zenodo_request_data)
    assert not list(dictdiffer.diff(result, expected_rdm_request_entry))
