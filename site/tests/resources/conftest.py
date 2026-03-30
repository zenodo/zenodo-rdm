# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test Zenodo resources."""

import pytest
from invenio_app import factory as app_factory


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return app_factory.create_api
