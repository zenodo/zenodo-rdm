# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test for OpenAIRE helpers."""

from copy import deepcopy

import pytest

from zenodo_rdm.openaire.utils import (
    OA_DATASET,
    OA_OTHER,
    OA_PUBLICATION,
    OA_SOFTWARE,
    openaire_id,
    openaire_link,
    openaire_type,
)


@pytest.fixture(scope="function")
def minimal_open_record(minimal_record):
    """Minimal record with open access."""
    r = deepcopy(minimal_record)

    # Test only open records
    r["access"] = {"record": "public", "files": "public"}
    return r


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        ("image-photo", OA_DATASET),
        ("other", OA_OTHER),
        ("publication-book", OA_PUBLICATION),
        ("publication", OA_PUBLICATION),
    ],
)
def test_openaire_type_serialization(
    running_app, minimal_open_record, resource_type, expected
):
    """Test OpenAIRE type.

    It uses only open records.
    """
    r = deepcopy(minimal_open_record)

    r["metadata"]["resource_type"] = {"id": resource_type}

    assert openaire_type(r) == expected


def test_embardoged_publication_serialization(running_app, minimal_record):
    """Test OpenAIRE serialization for an embargoed (restricted) publication."""
    r = deepcopy(minimal_record)

    r["metadata"]["resource_type"] = {"id": "publication"}

    # Non-open publications
    r["access_right"] = {
        "files": "restricted",
        "record": "restricted",
        "embargo": {"active": True},
    }
    assert openaire_type(r) is None


def test_funded_publication_serialization(
    running_app, minimal_record, ec_funded_community
):
    """Test a publication that is funded (e.g. has grants)."""
    r = deepcopy(minimal_record)

    r["metadata"]["resource_type"] = {"id": "publication"}

    # with grants
    r["metadata"]["funding"] = [{"funder": {"id": "someid"}, "award": {"id": "someid"}}]
    assert openaire_type(r) == OA_PUBLICATION

    # in ecfunded community
    del r["metadata"]["funding"]
    r["parent"] = {"communities": {"ids": [ec_funded_community.id]}}
    assert openaire_type(r) == OA_PUBLICATION
    r["parent"] = {"communities": {"ids": ["zenodo"]}}
    assert openaire_type(r) is None


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        ("software", "od______2659::47287d1800c112499a117ca17aa1909d"),
        ("other", "od______2659::47287d1800c112499a117ca17aa1909d"),
        ("dataset", "od______2659::204007f516ddcf0a452c2f22d48695ca"),
        ("publication", "od______2659::47287d1800c112499a117ca17aa1909d"),
    ],
)
def test_openaire_id(running_app, minimal_open_record, resource_type, expected):
    """Test OpenAIRE ID."""
    r = deepcopy(minimal_open_record)
    r["pids"] = {
        "doi": {"identifier": "10.5281/zenodo.123"},
        "oai": {"identifier": "oai:zenodo.org:123"},
    }
    r["metadata"]["resource_type"] = {"id": resource_type}
    assert openaire_id(r) == expected


@pytest.mark.parametrize(
    "resource_type,oatype",
    [
        ("software", OA_SOFTWARE),
        ("image-photo", OA_DATASET),
        ("other", OA_OTHER),
        ("dataset", OA_DATASET),
        ("publication", OA_PUBLICATION),
    ],
)
def test_openaire_link(running_app, minimal_open_record, resource_type, oatype):
    """Test OpenAIRE ID."""
    r = deepcopy(minimal_open_record)

    doi = "10.5281/zenodo.123"
    r["pids"] = {
        "doi": {"identifier": doi},
        "oai": {"identifier": "oai:zenodo.org:123"},
    }
    r["metadata"]["resource_type"] = {"id": resource_type}
    assert openaire_link(r) == f"https://explore.openaire.eu/search/{oatype}?pid={doi}"
