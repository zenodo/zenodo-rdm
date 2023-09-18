# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Tests for openaire serializer."""

import pytest
from zenodo_rdm.openaire.serializers import OpenAIREV1Serializer
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_access.permissions import system_identity


@pytest.fixture(scope="module")
def openaire_serializer():
    yield OpenAIREV1Serializer()


def test_record_serializer(running_app, minimal_record, openaire_serializer):
    serializer = openaire_serializer

    # Disable files, we don't care about files for this test.
    minimal_record["files"]["enabled"] = False

    # We use system identity since we just want a record to be serialized, we don't care about permissions.
    draft = records_service.create(system_identity, minimal_record)
    record = records_service.publish(id_=draft.id, identity=system_identity)

    serialized_record = serializer.dump_obj(record)
    assert serialized_record
