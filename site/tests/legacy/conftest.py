# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test legacy API."""

import pytest

from zenodo_rdm.legacy.resources import (
    LegacyFilesRESTResourceConfig,
    LegacyRecordResourceConfig,
)


@pytest.fixture
def deposit_url(test_app):
    """Deposit API URL."""
    host = test_app.config["SITE_API_URL"]
    return f"{host}{LegacyRecordResourceConfig.url_prefix}"


@pytest.fixture
def files_rest_url(test_app):
    """Files-REST API URL."""
    host = test_app.config["SITE_API_URL"]
    return f"{host}{LegacyFilesRESTResourceConfig.url_prefix}"
