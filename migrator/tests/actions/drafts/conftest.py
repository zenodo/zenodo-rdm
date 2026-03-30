# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Migrator tests configuration."""

from pathlib import Path

import pytest


@pytest.fixture()
def tx_files():
    """Transactions file paths."""
    testdata_dir = Path(__file__).parent / "testdata"
    assert testdata_dir.exists()
    return {f.stem: f for f in testdata_dir.iterdir() if f.is_file()}
