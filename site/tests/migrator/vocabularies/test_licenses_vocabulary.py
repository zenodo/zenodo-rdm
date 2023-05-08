# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test legacy licenses vocabulary."""

import pytest

from zenodo_rdm.legacy.vocabularies.licenses import legacy_to_rdm, rdm_to_legacy


@pytest.fixture
def legacy_license():
    """Legacy license id."""
    return "cc-zero"


@pytest.fixture
def legacy_aliased_license():
    """Aliased legacy license id."""
    return "CC0-1.0"


@pytest.fixture
def rdm_right():
    """RDM right id."""
    return "cc0-1.0"


def test_rdm_to_legacy(legacy_license, rdm_right):
    """Tests RDM to Legacy licenses mapping."""
    mapped_license = rdm_to_legacy(rdm_right)

    # RDM to legacy maps to the license id, not the alias
    assert mapped_license == legacy_license

    non_aliased_license = "oml"
    mapped_license = rdm_to_legacy(non_aliased_license)

    assert mapped_license == non_aliased_license

    # Unknown licenses return None
    test_license = "test"

    mapped_license = rdm_to_legacy(test_license)

    assert not mapped_license

    mapped_license = rdm_to_legacy(None)

    assert not mapped_license


def test_legacy_to_rdm(legacy_license, legacy_aliased_license, rdm_right):
    """Tests Legacy to RDM licenses mapping."""
    mapped_license = legacy_to_rdm(legacy_license)

    assert mapped_license == rdm_right

    mapped_license = legacy_to_rdm(legacy_aliased_license)

    assert mapped_license == rdm_right

    # Unknown licenses return None
    test_license = "test"

    mapped_license = legacy_to_rdm(test_license)

    assert not mapped_license

    mapped_license = legacy_to_rdm(None)

    assert not mapped_license
