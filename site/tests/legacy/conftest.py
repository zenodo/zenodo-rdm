# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test legacy API."""

import pytest

from zenodo_rdm.legacy.resources import LegacyRecordResourceConfig


@pytest.fixture
def deposit_url(test_app):
    """Deposit API URL."""
    host = test_app.config["SITE_API_URL"]
    return f"{host}{LegacyRecordResourceConfig.url_prefix}"
