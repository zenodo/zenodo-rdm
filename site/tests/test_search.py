# SPDX-FileCopyrightText: 2025-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test search API page size validation."""

import pytest


@pytest.fixture
def search_url(test_app):
    """Search API URL."""
    host = test_app.config["SITE_API_URL"]
    return f"{host}/records"


def test_guest_page_size_validation(client, search_url):
    """Guest users limited to 25 results per page."""
    # Guest: size=25 works
    res = client.get(f"{search_url}?size=25")
    assert res.status_code == 200

    # Guest: size=26 exceeds limit
    res = client.get(f"{search_url}?size=26")
    assert res.status_code == 400
    assert res.json == {
        "status": 400,
        "message": "A validation error occurred.",
        "errors": [
            {
                "field": "size",
                "messages": [
                    "Page size cannot be greater than 25. Please use authenticated requests to increase the limit to 100."
                ],
            }
        ],
    }


def test_authenticated_page_size_validation(client_with_login, search_url):
    """Authenticated users limited to 100 results per page."""
    # Auth: size=100 works
    res = client_with_login.get(f"{search_url}?size=100")
    assert res.status_code == 200

    # Auth: size=101 exceeds limit
    res = client_with_login.get(f"{search_url}?size=101")
    assert res.status_code == 400
    assert res.json == {
        "status": 400,
        "message": "A validation error occurred.",
        "errors": [
            {
                "field": "size",
                "messages": ["Page size cannot be greater than 100."],
            }
        ],
    }


@pytest.mark.parametrize(
    "content_type",
    [
        "application/dcat+xml",
        "application/json",
        'application/ld+json;profile=\\"https://datapackage.org/profiles/2.0/datapackage.json\\"',
        "application/ld+json",
        "application/linkset+json",
        "application/marcxml+xml",
        "application/vnd.citationstyles.csl+json",
        "application/vnd.datacite.datacite+json",
        "application/vnd.datacite.datacite+xml",
        "application/vnd.geo+json",
        "application/vnd.inveniordm.v1.full+csv",
        "application/vnd.inveniordm.v1.simple+csv",
        "application/vnd.inveniordm.v1+json",
        "application/vnd.zenodo.v1+json",
        "application/x-bibtex",
        "application/x-datacite+xml",
        "application/x-dc+xml",
        "text/x-bibliography",
    ],
)
def test_search_serializers(
    publish_record, minimal_record, client, search_url, content_type
):
    """Searching for records with a serializer format in the accept headers works."""
    record = publish_record(dict(minimal_record, files={"enabled": False}))
    record_doi = record["pids"]["doi"]["identifier"]

    res = client.get(f"{search_url}", headers={"Accept": content_type})
    assert res.status_code == 200
    if content_type != "application/vnd.geo+json":
        assert record_doi in res.text
