# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Rules for curation."""

from flask import current_app
from invenio_records_resources.proxies import current_service_registry


def award_acronym_in_description(record):
    """Check if EU award name in record description."""

    award_service = current_service_registry.get("awards")
    description = record.metadata["description"]
    funding = record.metadata["funding"]

    for f in funding:
        if f["funder"]["id"] == "00k4n6c32":
            if "award" in f:
                award = award_service.record_cls.pid.resolve(f["award"]["id"])
                if award["acronym"].lower() in description.lower():
                    return True
    return False


def award_acronym_in_title(record):
    """Check if EU award name in record title."""

    award_service = current_service_registry.get("awards")
    title = record.metadata["title"]
    funding = record.metadata["funding"]

    for f in funding:
        if f["funder"]["id"] == "00k4n6c32":
            if "award" in f:
                award = award_service.record_cls.pid.resolve(f["award"]["id"])
                if award["acronym"].lower() in title.lower():
                    return True
    return False


def test_phrases_in_record(record):
    """Check if test words in record."""

    test_phrases = current_app.config.get("CURATION_TEST_PHRASES")
    record_data = record.metadata["title"] + " " + record.metadata["description"]

    for word in test_phrases:
        if word.lower() in record_data.lower():
            return True
    return False
