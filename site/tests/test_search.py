# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
