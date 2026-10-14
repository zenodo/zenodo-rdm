# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Legacy extra formats must not reveal non-visible drafts or records."""

from io import BytesIO

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as service

MIMETYPE = "application/custom+xml"

DEPOSIT_DATA = {
    "metadata": {
        "upload_type": "dataset",
        "title": "Extra formats visibility",
        "creators": [{"name": "Doe, John"}],
        "publication_date": "2020-01-01",
        "description": "Regression test",
        "access_right": "open",
    }
}


def _create_deposit(client, deposit_url, headers, publish=True):
    """Create a deposit with one file, optionally publishing it."""
    res = client.post(deposit_url, json=DEPOSIT_DATA, headers=headers)
    assert res.status_code == 201, res.json
    links = res.json["links"]
    recid = str(res.json["id"])
    res = client.post(
        links["files"],
        data={"file": (BytesIO(b"data"), "data.txt"), "name": "data.txt"},
    )
    assert res.status_code == 201, res.json
    if publish:
        res = client.post(links["publish"])
        assert res.status_code == 202, res.json
    return recid, links


def _formats_responses(client, deposit_url, recid):
    """Return (status, body) of GET and OPTIONS on the deposit formats URL."""
    url = f"{deposit_url}/{recid}/formats"
    get = client.get(url, query_string={"mimetype": MIMETYPE})
    options = client.options(url)
    return (get.status_code, get.json), (options.status_code, options.json)


@pytest.fixture()
def objects(client, deposit_url, headers, uploader):
    """Create one object per visibility state, all owned by ``uploader``."""
    client = uploader.api_login(client)

    public, _ = _create_deposit(client, deposit_url, headers)

    # Public record with an open edit draft holding an extra format.
    public_with_draft, links = _create_deposit(client, deposit_url, headers)
    res = client.post(links["edit"])
    assert res.status_code == 201, res.json
    res = client.put(
        f"{deposit_url}/{public_with_draft}/formats",
        data=BytesIO(b"draft format"),
        headers={"Content-Type": MIMETYPE},
    )
    assert res.status_code == 200, res.json

    unpublished, _ = _create_deposit(client, deposit_url, headers, publish=False)

    restricted, _ = _create_deposit(client, deposit_url, headers)
    draft = service.edit(system_identity, restricted)
    data = draft.data
    data["access"]["record"] = "restricted"
    service.update_draft(system_identity, restricted, data)
    service.publish(system_identity, restricted)

    uploader.api_logout(client)
    return {
        "public": public,
        "public_with_draft": public_with_draft,
        "unpublished": unpublished,
        "restricted": restricted,
    }


def _assert_not_visible(client, deposit_url, recid):
    """Both GET and OPTIONS answer 404."""
    for status, _ in _formats_responses(client, deposit_url, recid):
        assert status == 404


def test_anonymous_formats_visibility(client, deposit_url, objects):
    """Anonymous callers only see what is public."""
    _assert_not_visible(client, deposit_url, "999999999")
    _assert_not_visible(client, deposit_url, objects["unpublished"])
    _assert_not_visible(client, deposit_url, objects["restricted"])

    # An open edit draft must be indistinguishable from no draft.
    assert _formats_responses(
        client, deposit_url, objects["public_with_draft"]
    ) == _formats_responses(client, deposit_url, objects["public"])


def test_anonymous_formats_put_does_not_reveal_draft(client, deposit_url, objects):
    """Writes on a public record answer the same with or without an edit draft."""
    statuses = []
    for recid in (objects["public"], objects["public_with_draft"]):
        res = client.put(
            f"{deposit_url}/{recid}/formats",
            data=BytesIO(b"x"),
            headers={"Content-Type": MIMETYPE},
        )
        statuses.append(res.status_code)
    assert statuses[0] == statuses[1]
    assert statuses[0] in (401, 403)

    res = client.put(
        f"{deposit_url}/{objects['unpublished']}/formats",
        data=BytesIO(b"x"),
        headers={"Content-Type": MIMETYPE},
    )
    assert res.status_code == 404


def test_other_user_formats_visibility(client, deposit_url, objects, test_user):
    """Another authenticated user only sees what is public."""
    client = test_user.api_login(client)

    _assert_not_visible(client, deposit_url, objects["unpublished"])
    _assert_not_visible(client, deposit_url, objects["restricted"])
    assert _formats_responses(
        client, deposit_url, objects["public_with_draft"]
    ) == _formats_responses(client, deposit_url, objects["public"])


def test_owner_sees_draft_formats(client, deposit_url, objects, uploader):
    """The owner still reads the extra formats of their edit draft."""
    client = uploader.api_login(client)

    url = f"{deposit_url}/{objects['public_with_draft']}/formats"
    res = client.get(url, query_string={"mimetype": MIMETYPE})
    assert res.status_code == 200
    assert res.data == b"draft format"

    res = client.options(url)
    assert res.status_code == 200
    assert [f["key"] for f in res.json] == [MIMETYPE]
