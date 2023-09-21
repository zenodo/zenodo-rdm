# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE tests fixtures."""

from unittest.mock import MagicMock, patch

import pytest
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service as records_service

from zenodo_rdm.openaire.serializers import OpenAIREV1Serializer


@pytest.fixture(scope="module")
def openaire_serializer():
    """Yield the OpenAIRE serializer."""
    yield OpenAIREV1Serializer()


@pytest.fixture(scope="module")
def mocked_session():
    """Mock requests.Session() object."""

    class MockedReponse(MagicMock):
        ok = True
        text = ""
        status_code = 200

    # Patch with default ``MagicMock``
    with patch("zenodo_rdm.openaire.utils.Session", MagicMock) as mock:
        mock.post = MagicMock(return_value=MockedReponse)
        yield mock


@pytest.fixture(scope="function")
def openaire_api_endpoint(running_app):
    """Return OpenAIRE endpoint."""
    openaire_api_url = running_app.app.config["OPENAIRE_API_URL"]
    return f"{openaire_api_url}/feedObject"


@pytest.fixture(scope="function")
def openaire_record_data(minimal_record):
    """Extend the record data defined in the fixture ``minimal_record``."""
    # Disable files, we don't care about files for this test.
    minimal_record["files"]["enabled"] = False

    # Funder and award were previously created in conftest
    minimal_record["metadata"]["funding"] = [
        {"funder": {"id": "00rbzpz17"}, "award": {"id": "00rbzpz17::755021"}}
    ]
    return minimal_record


@pytest.fixture(scope="function")
def openaire_record(openaire_record_data, create_record):
    """Record for openaire testing."""
    return create_record(openaire_record_data)


@pytest.fixture(scope="module")
def create_record():
    """Fixture provides a factory to create records."""

    def _add_to_community(record, community):
        """Add a record to a community."""
        record.parent.communities.add(community._record, default=False)
        record.parent.commit()
        record.commit()
        db.session.commit()
        records_service.indexer.index(record, arguments={"refresh": True})
        return record

    def _create_record(record_data, community=None):
        """Create a record."""
        draft = records_service.create(system_identity, record_data)
        if community:
            _add_to_community(draft._record, community)
        record = records_service.publish(id_=draft.id, identity=system_identity)
        return record

    return _create_record
