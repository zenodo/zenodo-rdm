# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Tests for openaire serializer."""

expected_keys = (
    "language",
    "type",
    "resourceType",
    "originalId",
    "title",
    "url",
    "authors",
    "licenseCode",
    "publisher",
    "collectedFromId",
    "hostedById",
    "pids",
    "contexts",
    "linksToProjects",
    "version",
)


def test_record_serializer(
    running_app, openaire_serializer, create_record, openaire_record_data, community
):
    """Test a simple record."""
    serializer = openaire_serializer
    record = create_record(openaire_record_data, community)

    serialized_record = serializer.dump_obj(record.data)
    assert serialized_record
    assert all([k for k in expected_keys if k in serialized_record])
    assert (
        len([pid for pid in serialized_record["pids"] if pid["type"] in ("doi", "oai")])
        == 2
    )


def test_embargoed_record(
    running_app, openaire_record_data, create_record, openaire_serializer, community
):
    """Test an embargoed record."""
    serializer = openaire_serializer
    openaire_record_data["access"] = {
        "files": "restricted",
        "record": "restricted",
        "embargo": {"active": True, "until": "2500-12-12"},
    }
    record = create_record(openaire_record_data, community)
    serialized_record = serializer.dump_obj(record.data)
    assert serialized_record
    assert all([k for k in expected_keys if k in serialized_record])
    assert serialized_record["licenseCode"] == "EMBARGO"
    assert serialized_record["embargoEndDate"]


def test_closed_record(
    running_app, openaire_record_data, create_record, openaire_serializer, community
):
    """Test a closed record.

    In RDM, a closed record does not exist by design. However, we can map it following legacy Zenodo logic.
    A record is closed if it's restricted AND does not allow any access requests (e.g. it's totally restricted to only the owner).
    """
    serializer = openaire_serializer
    openaire_record_data["parent"] = {
        "access": {
            "settings": {
                "allow_user_requests": False,
                "allow_guest_requests": False,
            }
        },
    }

    record = create_record(openaire_record_data, community)
    serialized_record = serializer.dump_obj(record.data)
    assert serialized_record
    assert all([k for k in expected_keys if k in serialized_record])
    assert serialized_record["licenseCode"] == "CLOSED"
