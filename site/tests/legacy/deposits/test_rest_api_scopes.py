# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test OAuth scope enforcement on the legacy deposit REST API."""

from io import BytesIO

import pytest
from invenio_oauth2server.models import Token

from zenodo_rdm.legacy.scopes import (
    LEGACY_ENDPOINT_SCOPES,
    deposit_actions_scope,
    deposit_write_scope,
)

WRITE = deposit_write_scope.id
ACTIONS = deposit_actions_scope.id


@pytest.fixture()
def make_token(db, uploader):
    """Create a personal access token for the uploader with the given scopes."""

    def _make(scopes):
        token = Token.create_personal("test-token", uploader.id, scopes=scopes)
        db.session.commit()
        return token.access_token

    return _make


def _auth(headers, token):
    """Add a bearer token to the request headers."""
    return {**headers, "Authorization": f"Bearer {token}"}


def _upload(client, links, headers, name="data.txt"):
    """Upload a file to a deposit through the multipart endpoint."""
    return client.post(
        links["files"],
        headers={"Authorization": headers["Authorization"]},
        data={"name": name, "file": (BytesIO(b"data"), name)},
        content_type="multipart/form-data",
    )


def _create(client, deposit_url, headers, test_data):
    """Create a deposit and return its links."""
    res = client.post(deposit_url, json=test_data, headers=headers)
    assert res.status_code == 201, res.json
    return res.json["links"]


def _published(client, deposit_url, headers, test_data, make_token):
    """Publish a deposit with a fully scoped token and return its links."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _create(client, deposit_url, full, test_data)
    assert _upload(client, links, full).status_code == 201
    res = client.post(links["publish"], headers=full)
    assert res.status_code == 202, res.json
    return links


@pytest.mark.parametrize("scopes", [[], ["user:email"]])
def test_token_without_deposit_scopes(
    client, deposit_url, headers, test_data, make_token, scopes
):
    """A token without deposit scopes cannot create, update, upload or publish."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _create(client, deposit_url, full, test_data)
    assert _upload(client, links, full).status_code == 201

    limited = _auth(headers, make_token(scopes))
    res = client.post(deposit_url, json=test_data, headers=limited)
    assert res.status_code == 403
    res = client.put(links["self"], json=test_data, headers=limited)
    assert res.status_code == 403
    assert _upload(client, links, limited, "other.txt").status_code == 403
    assert client.post(links["publish"], headers=limited).status_code == 403

    # The draft was not published
    res = client.get(links["self"], headers=full)
    assert res.json["submitted"] is False
    assert res.json["state"] == "unsubmitted"


@pytest.mark.parametrize("scopes", [[], [ACTIONS]])
def test_token_without_write_scope(
    client, deposit_url, headers, test_data, make_token, scopes
):
    """Deposit writes require the deposit:write scope."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _create(client, deposit_url, full, test_data)
    assert _upload(client, links, full).status_code == 201

    limited = _auth(headers, make_token(scopes))
    assert client.post(deposit_url, json=test_data, headers=limited).status_code == 403
    res = client.put(links["self"], json=test_data, headers=limited)
    assert res.status_code == 403
    assert _upload(client, links, limited, "other.txt").status_code == 403

    # Files-REST and extra formats
    file_url = f"{links['bucket']}/other.txt"
    res = client.put(
        file_url,
        data=BytesIO(b"data"),
        headers={**limited, "content-type": "application/octet-stream"},
    )
    assert res.status_code == 403
    res = client.delete(f"{links['bucket']}/data.txt", headers=limited)
    assert res.status_code == 403
    res = client.put(
        f"{links['self']}/formats",
        data=BytesIO(b"custom xml"),
        headers={
            "Authorization": limited["Authorization"],
            "Content-Type": "application/custom+xml",
        },
    )
    assert res.status_code == 403

    assert client.delete(links["self"], headers=limited).status_code == 403
    # Nothing was changed by the limited token
    assert client.get(links["self"], headers=full).status_code == 200


@pytest.mark.parametrize("scopes", [[], ["user:email"]])
def test_reads_do_not_need_deposit_scopes(
    client, deposit_url, headers, test_data, make_token, scopes
):
    """Reading own deposits and their files works without deposit scopes."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _create(client, deposit_url, full, test_data)
    assert _upload(client, links, full).status_code == 201
    file_id = client.get(links["files"], headers=full).json[0]["id"]

    limited = _auth(headers, make_token(scopes))
    assert client.get(deposit_url, headers=limited).status_code == 200
    assert client.get(links["self"], headers=limited).status_code == 200
    assert client.get(links["files"], headers=limited).status_code == 200
    res = client.get(f"{links['files']}/{file_id}", headers=limited)
    assert res.status_code == 200


def test_write_scope_cannot_run_actions(
    client, deposit_url, headers, test_data, make_token
):
    """A deposit:write token can upload but not publish, edit or discard."""
    write = _auth(headers, make_token([WRITE]))

    links = _create(client, deposit_url, write, test_data)
    assert client.get(links["self"], headers=write).status_code == 200
    assert client.put(links["self"], json=test_data, headers=write).status_code == 200
    assert _upload(client, links, write).status_code == 201

    assert client.post(links["publish"], headers=write).status_code == 403
    assert client.post(links["discard"], headers=write).status_code == 403

    # Plain DELETE of an unpublished draft only needs deposit:write
    assert client.delete(links["self"], headers=write).status_code == 204

    published = _published(client, deposit_url, headers, test_data, make_token)
    assert client.post(published["edit"], headers=write).status_code == 403
    assert client.post(published["newversion"], headers=write).status_code == 403


def test_write_and_actions_scopes(client, deposit_url, headers, test_data, make_token):
    """A token with both scopes can run the whole deposit flow."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _published(client, deposit_url, headers, test_data, make_token)

    res = client.post(links["edit"], headers=full)
    assert res.status_code == 201, res.json
    res = client.post(links["discard"], headers=full)
    assert res.status_code == 204
    res = client.post(links["newversion"], headers=full)
    assert res.status_code == 201, res.json


def test_query_string_token_is_scoped(
    client, deposit_url, headers, test_data, make_token
):
    """Scopes also apply to tokens passed as ``?access_token=``."""
    token = make_token([WRITE])
    qs = {"access_token": token}

    res = client.post(deposit_url, json=test_data, headers=headers, query_string=qs)
    assert res.status_code == 201, res.json
    links = res.json["links"]
    res = client.post(
        links["files"],
        data={"name": "data.txt", "file": (BytesIO(b"data"), "data.txt")},
        content_type="multipart/form-data",
        query_string=qs,
    )
    assert res.status_code == 201

    res = client.post(links["publish"], headers=headers, query_string=qs)
    assert res.status_code == 403


def test_anonymous_requests(client, deposit_url, headers, test_data, make_token):
    """Anonymous requests to deposit endpoints are rejected as unauthenticated."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _create(client, deposit_url, full, test_data)

    assert client.post(deposit_url, json=test_data, headers=headers).status_code == 401
    assert client.post(links["publish"], headers=headers).status_code == 401
    assert client.delete(links["self"], headers=headers).status_code == 401


def test_session_login_is_not_scoped(
    client_with_login, deposit_url, headers, test_data
):
    """Users logged in with a session are not subject to token scopes."""
    client = client_with_login
    links = _create(client, deposit_url, headers, test_data)
    res = client.post(
        links["files"],
        data={"name": "data.txt", "file": (BytesIO(b"data"), "data.txt")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 201
    assert client.post(links["publish"], headers=headers).status_code == 202


def test_scoped_endpoints_exist(app):
    """Every endpoint in the scope map is a registered API view."""
    api_app = app.wsgi_app.mounts["/api"]
    missing = set(LEGACY_ENDPOINT_SCOPES) - set(api_app.view_functions)
    assert not missing


def test_cors_preflight_is_not_scoped(
    client, deposit_url, headers, test_data, make_token
):
    """CORS preflight requests carry no credentials and are not rejected."""
    full = _auth(headers, make_token([WRITE, ACTIONS]))
    links = _create(client, deposit_url, full, test_data)

    preflight = {
        "Origin": "https://example.org",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization, content-type",
    }
    for url in [
        deposit_url,
        links["self"],
        links["files"],
        links["publish"],
        f"{links['bucket']}/data.txt",
    ]:
        res = client.options(url, headers=preflight)
        assert res.status_code == 200, url
        assert "Access-Control-Allow-Origin" in res.headers, url
