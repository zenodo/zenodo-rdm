# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test that internal notes are only readable and writable by the system."""

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from marshmallow_utils.permissions import FieldPermissionError

MARKER = "zzsecretmarker"
RDM_JSON = {"Accept": "application/vnd.inveniordm.v1+json"}


@pytest.fixture()
def urls(test_app):
    """API and UI base URLs."""
    return test_app.config["SITE_API_URL"], test_app.config["SITE_UI_URL"]


@pytest.fixture()
def owned_noted_record(running_app, minimal_record, uploader):
    """Publish a record owned by the uploader, with a note added by the system."""
    data = dict(minimal_record, files={"enabled": False})
    draft = records_service.create(uploader.identity, data)
    records_service.update_draft(
        system_identity,
        draft.id,
        dict(data, internal_notes=[{"note": f"Flagged as {MARKER}"}]),
    )
    record = records_service.publish(uploader.identity, draft.id)
    records_service.indexer.index(record._record, arguments={"refresh": True})
    assert _system_notes(record.id) == [f"Flagged as {MARKER}"]
    return record.id


def _editable(draft):
    """Fields a deposit form sends back when saving a draft."""
    keys = ("metadata", "access", "files", "custom_fields")
    return {k: draft[k] for k in keys if k in draft}


def _system_notes(recid, draft=False):
    read = records_service.read_draft if draft else records_service.read
    return [n["note"] for n in read(system_identity, recid).data["internal_notes"]]


def test_record_serializations_hide_notes(
    client, urls, uploader, owned_noted_record, test_app
):
    """No REST serialization exposes notes, to anonymous users or to the owner."""
    api, _ = urls
    recid = owned_noted_record
    mimetypes = list(test_app.config["RDM_RECORDS_SERIALIZERS"])
    for logged_in in (False, True):
        if logged_in:
            uploader.api_login(client)
        for mimetype in mimetypes:
            res = client.get(f"{api}/records/{recid}", headers={"Accept": mimetype})
            assert res.status_code in (200, 406), mimetype
            assert MARKER not in res.get_data(as_text=True), mimetype
            assert "internal_notes" not in res.get_data(as_text=True), mimetype


def test_search_results_hide_notes(client, urls, uploader, owned_noted_record):
    """Search hits never contain notes."""
    api, _ = urls
    res = client.get(f"{api}/records", query_string={"q": f"id:{owned_noted_record}"})
    assert res.json["hits"]["total"] == 1
    assert "internal_notes" not in res.json["hits"]["hits"][0]

    uploader.api_login(client)
    res = client.get(f"{api}/user/records")
    hits = res.json["hits"]["hits"]
    assert owned_noted_record in {str(h["id"]) for h in hits}
    assert all("internal_notes" not in h for h in hits)


def test_ui_and_oai_hide_notes(client, urls, uploader, owned_noted_record):
    """Landing page, export pages and OAI-PMH do not show notes."""
    _, ui = urls
    recid = owned_noted_record
    oai_id = records_service.read(system_identity, recid).data["pids"]["oai"][
        "identifier"
    ]
    pages = [f"{ui}/records/{recid}"] + [
        f"{ui}/records/{recid}/export/{fmt}"
        for fmt in ("json", "zenodo", "datacite-json", "datacite-xml", "dublincore")
    ]
    pages += [
        f"{ui}/oai2d?verb=GetRecord&identifier={oai_id}&metadataPrefix={prefix}"
        for prefix in (
            "oai_dc",
            "marcxml",
            "marc21",
            "oai_datacite",
            "datacite",
            "dcat",
        )
    ]
    for logged_in in (False, True):
        if logged_in:
            uploader.login(client)
        for page in pages:
            res = client.get(page)
            assert res.status_code in (200, 404), page
            assert MARKER not in res.get_data(as_text=True), page


def test_owner_edit_hides_and_keeps_notes(client, urls, uploader, owned_noted_record):
    """The owner cannot see notes on their draft, and editing keeps them."""
    api, _ = urls
    recid = owned_noted_record
    uploader.api_login(client)

    res = client.post(f"{api}/records/{recid}/draft", headers=RDM_JSON)
    assert res.status_code == 201
    draft = res.json
    assert "internal_notes" not in draft

    res = client.put(
        f"{api}/records/{recid}/draft", json=_editable(draft), headers=RDM_JSON
    )
    assert res.status_code == 200
    assert "internal_notes" not in res.json
    assert _system_notes(recid, draft=True) == [f"Flagged as {MARKER}"]

    res = client.post(f"{api}/records/{recid}/draft/actions/publish")
    assert res.status_code == 202
    assert _system_notes(recid) == [f"Flagged as {MARKER}"]


def test_owner_cannot_write_notes(uploader, owned_noted_record):
    """The owner cannot add, replace or clear notes."""
    recid = owned_noted_record
    draft = records_service.edit(uploader.identity, recid).to_dict()

    for notes in ([{"note": "forged"}], []):
        data = dict(_editable(draft), internal_notes=notes)
        with pytest.raises(FieldPermissionError):
            records_service.update_draft(uploader.identity, recid, data)
        assert _system_notes(recid, draft=True) == [f"Flagged as {MARKER}"]


def test_user_cannot_create_with_notes(running_app, uploader, minimal_record):
    """A user cannot create a draft with notes."""
    data = dict(minimal_record, files={"enabled": False})
    with pytest.raises(FieldPermissionError):
        records_service.create(
            uploader.identity, dict(data, internal_notes=[{"note": "forged"}])
        )


def test_superuser_can_read_notes(superuser, owned_noted_record):
    """Superusers (Zenodo staff) can read notes."""
    notes = records_service.read(superuser.identity, owned_noted_record).data[
        "internal_notes"
    ]
    assert [n["note"] for n in notes] == [f"Flagged as {MARKER}"]
