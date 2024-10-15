# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test OpenAIRE components."""

from unittest import mock

from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_rdm_records.services.components import DefaultRecordsComponents

from zenodo_rdm.openaire.records.components import OpenAIREComponent
from zenodo_rdm.openaire.utils import get_openaire_id


def test_on_publish(
    running_app,
    monkeypatch,
    create_record,
    openaire_record_data,
    community,
    mocked_session,
    openaire_api_endpoint,
    openaire_serializer,
    enable_openaire_indexing,
):
    """Test on publish components"""

    # Only for this test, modify record service components
    monkeypatch.setitem(
        running_app.app.config,
        "RDM_RECORDS_SERVICE_COMPONENTS",
        DefaultRecordsComponents + [OpenAIREComponent],
    )

    record = create_record(openaire_record_data, community)
    assert record

    serialized_record = openaire_serializer.dump_obj(record.data)

    post_endpoint = f"{openaire_api_endpoint}/results/feedObject"
    mocked_session.post.assert_called_once_with(
        post_endpoint,
        json=serialized_record,
        timeout=30,
    )


def test_on_delete(
    running_app,
    monkeypatch,
    openaire_record_data,
    community,
    create_record,
    openaire_serializer,
    mocked_session,
    openaire_api_endpoint,
    enable_openaire_indexing,
):
    """Test on delete component."""

    # Only for this test, modify record service components
    monkeypatch.setitem(
        running_app.app.config,
        "RDM_RECORDS_SERVICE_COMPONENTS",
        DefaultRecordsComponents + [OpenAIREComponent],
    )

    record = create_record(openaire_record_data, community)
    assert record

    recid = record["id"]
    records_service.delete_record(system_identity, recid, {})

    serialized_record = openaire_serializer.dump_obj(record.data)

    post_endpoint = f"{openaire_api_endpoint}/results/feedObject"
    mocked_session.post.assert_called_once_with(
        post_endpoint, json=serialized_record, timeout=30
    )

    # NOTE: It would be better if we had a stable/deterministic DOI for the record
    # so we could hardcode here the OpenAIRE ID based on the md5 of the DOI
    openaire_id = get_openaire_id(record.data)
    mocked_session.delete.assert_called_once_with(
        f"{openaire_api_endpoint}/result/{openaire_id}"
    )


def test_on_restore(
    running_app,
    monkeypatch,
    openaire_record_data,
    community,
    create_record,
    openaire_serializer,
    mocked_session,
    openaire_api_endpoint,
    enable_openaire_indexing,
):
    """Test on restore component."""

    # Only for this test, modify record service components
    monkeypatch.setitem(
        running_app.app.config,
        "RDM_RECORDS_SERVICE_COMPONENTS",
        DefaultRecordsComponents + [OpenAIREComponent],
    )

    record = create_record(openaire_record_data, community)
    assert record

    recid = record["id"]

    records_service.delete_record(system_identity, recid, {})
    records_service.restore_record(system_identity, recid)

    serialized_record = openaire_serializer.dump_obj(record.data)

    post_endpoint = f"{openaire_api_endpoint}/results/feedObject"
    # HTTP POST will be called twice (one to create the record and one to restore it)
    post_calls = [
        mock.call(post_endpoint, json=serialized_record, timeout=30),
        mock.call(post_endpoint, json=serialized_record, timeout=30),
    ]

    # HTTP DELETE will be called once, when the record is deleted
    openaire_id = get_openaire_id(record.data)
    delete_calls = [
        mock.call(f"{openaire_api_endpoint}/result/{openaire_id}"),
    ]

    mocked_session.post.assert_has_calls(post_calls)
    mocked_session.delete.assert_has_calls(delete_calls)
