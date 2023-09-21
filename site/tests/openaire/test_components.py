# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test OpenAIRE components."""

import json

from invenio_rdm_records.services.components import DefaultRecordsComponents

from zenodo_rdm.openaire.records.components import OpenAIREComponent


def test_on_publish(
    running_app,
    monkeypatch,
    create_record,
    openaire_record_data,
    community,
    mocked_session,
    openaire_api_endpoint,
    openaire_serializer,
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

    mocked_session.post.assert_called_once_with(
        openaire_api_endpoint, data=json.dumps(serialized_record), timeout=10
    )
