# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared fixtures: a fake Zenodo API behind ``httpx.MockTransport``."""

import json

import httpx
import pytest
from mcp import Client

from zenodo_mcp.client import Settings
from zenodo_mcp.server import create_server

RECORD = {
    "id": "123",
    "is_published": True,
    "is_draft": False,
    "status": "published",
    "pids": {"doi": {"identifier": "10.5281/zenodo.123"}},
    "parent": {"pids": {"doi": {"identifier": "10.5281/zenodo.122"}}},
    "versions": {"is_latest": True},
    "metadata": {
        "title": "Light curves of HD 128329",
        "publication_date": "2026-01-01",
        "resource_type": {"id": "dataset"},
        "creators": [
            {
                "person_or_org": {
                    "name": "Curie, Marie",
                    "identifiers": [
                        {"scheme": "orcid", "identifier": "0000-0000-0000-0001"}
                    ],
                },
                "affiliations": [{"name": "CERN"}],
            }
        ],
        "description": "<p>Photometry <b>data</b></p>",
        "rights": [{"id": "cc-by-4.0"}],
        "subjects": [{"subject": "astronomy"}],
    },
    "access": {"record": "public", "files": "public"},
    "files": {"count": 1, "total_bytes": 10},
    "stats": {"this_version": {"unique_views": 5, "unique_downloads": 2}},
    "links": {"self_html": "https://zenodo.org/records/123"},
}


class FakeZenodo:
    """Records every request and answers from a route table."""

    def __init__(self):
        self.requests: list[httpx.Request] = []
        self.routes: dict[tuple[str, str], tuple[int, object]] = {}

    def route(self, method, path, status=200, body=None):
        self.routes[(method, path)] = (status, body)

    def handler(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        key = (request.method, request.url.path)
        if key not in self.routes:
            return httpx.Response(404, json={"status": 404, "message": "not found"})
        status, body = self.routes[key]
        if body is None:
            return httpx.Response(status)
        return httpx.Response(status, json=body)

    def sent(self, method, path):
        """Return the decoded JSON bodies sent to ``method path``."""
        return [
            json.loads(r.content) if r.content else None
            for r in self.requests
            if r.method == method and r.url.path == path
        ]


@pytest.fixture
def fake():
    return FakeZenodo()


@pytest.fixture
def make_client(fake):
    def _make(token=None, read_only=False):
        settings = Settings(
            base_url="https://zenodo.test", token=token, read_only=read_only
        )
        server = create_server(settings, transport=httpx.MockTransport(fake.handler))
        return Client(server)

    return _make
