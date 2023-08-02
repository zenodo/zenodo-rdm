# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

import tempfile

import pytest


@pytest.fixture(scope="function")
def tmp_dir():
    """Yields a temporary directory."""
    tmp_dir = tempfile.TemporaryDirectory()
    yield tmp_dir
    tmp_dir.cleanup()
