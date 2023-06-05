# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test Zenodo requests."""

import pytest
from invenio_app import factory as app_factory


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return app_factory.create_api
