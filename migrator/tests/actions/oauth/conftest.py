# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator community actions tests configuration."""

from pathlib import Path

import pytest


# FIXME: deduplicate from actions/communities tests
@pytest.fixture()
def tx_files_tokens():
    """Transactions file paths."""
    testdata_dir = Path(__file__).parent / "testdata" / "tokens"
    assert testdata_dir.exists()
    return {f.stem: f for f in testdata_dir.iterdir() if f.is_file()}


@pytest.fixture()
def tx_files_applications():
    """Transactions file paths."""
    testdata_dir = Path(__file__).parent / "testdata" / "applications"
    assert testdata_dir.exists()
    return {f.stem: f for f in testdata_dir.iterdir() if f.is_file()}


@pytest.fixture()
def tx_files_linked_accounts():
    """Transactions file paths."""
    testdata_dir = Path(__file__).parent / "testdata" / "linked_accounts"
    assert testdata_dir.exists()
    return {f.stem: f for f in testdata_dir.iterdir() if f.is_file()}
