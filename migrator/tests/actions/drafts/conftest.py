# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

from pathlib import Path

import pytest


@pytest.fixture()
def tx_files():
    """Transactions file paths."""
    testdata_dir = Path(__file__).parent / "testdata"
    assert testdata_dir.exists()
    return {f.stem: f for f in testdata_dir.iterdir() if f.is_file()}
