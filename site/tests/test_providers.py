# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test Zenodo PID providers."""

import copy

import pytest
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.services.errors import ValidationErrorWithMessageAsList


def _external_doi_record(minimal_record, doi):
    data = copy.deepcopy(minimal_record)
    data["files"]["enabled"] = False
    data["pids"] = {"doi": {"identifier": doi, "provider": "external"}}
    return data


def test_duplicate_external_doi_names_existing_record(
    running_app, uploader, minimal_record, search_clear
):
    """A duplicate external DOI error points to the record already using it."""
    service = current_rdm_records_service
    identity = uploader.identity
    doi = "10.1234/external.1"

    draft = service.create(identity, _external_doi_record(minimal_record, doi))
    first = service.publish(identity, draft.id)

    second = service.create(identity, _external_doi_record(minimal_record, doi))
    with pytest.raises(ValidationErrorWithMessageAsList) as exc:
        service.publish(identity, second.id)

    messages = exc.value.messages
    assert f"/records/{first.id}" in str(messages)
    assert "already used by the record" in str(messages)
