# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test legacy API."""

import pytest

from zenodo_rdm.legacy.resources import LegacyRecordResourceConfig


@pytest.fixture
def deposit_url():
    """Deposit API URL."""
    return f"/api{LegacyRecordResourceConfig.url_prefix}"
