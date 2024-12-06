# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Rules for curation."""

from datetime import datetime

from flask import current_app
from invenio_records_resources.proxies import current_service_registry


def award_acronym_in_description(record):
    """Check if EU award name in record description."""
    award_service = current_service_registry.get("awards")
    description = record.metadata.get("description")
    if not description:
        return False

    funding = record.metadata.get("funding", [])
    for f in funding:
        if f["funder"]["id"] == "00k4n6c32":
            if award_id := f.get("award", {}).get("id"):
                award = award_service.record_cls.pid.resolve(award_id)
                if award.get("acronym") and (
                    award.get("acronym").lower() in description.lower()
                ):
                    return True
    return False


def award_acronym_in_title(record):
    """Check if EU award name in record title."""
    award_service = current_service_registry.get("awards")
    title = record.metadata["title"]
    funding = record.metadata["funding"]

    for f in funding:
        if f["funder"]["id"] == "00k4n6c32":
            if award_id := f.get("award", {}).get("id"):
                award = award_service.record_cls.pid.resolve(award_id)
                if award.get("acronym") and (
                    award.get("acronym").lower() in title.lower()
                ):
                    return True
    return False


def test_phrases_in_record(record):
    """Check if test words in record."""
    test_phrases = current_app.config.get("CURATION_TEST_PHRASES")
    record_data = (
        record.metadata["title"] + " " + record.metadata.get("description", "")
    )

    for word in test_phrases:
        if word.lower() in record_data.lower():
            return True
    return False


def published_before_award_start(record):
    """Check if published before award start date."""
    award_service = current_service_registry.get("awards")

    for f in record.metadata["funding"]:
        if f["funder"]["id"] == "00k4n6c32":
            if award_id := f.get("award", {}).get("id"):
                award = award_service.record_cls.pid.resolve(award_id)
                if award.get("start_date") and (
                    record.created < datetime.fromisoformat(award.get("start_date"))
                ):
                    return True
    return False


def user_verified(record):
    """Check if user is verified."""
    is_verified = (
        getattr(record.parent, "is_verified", None)
        if hasattr(record, "parent")
        else getattr(record, "is_verified", False)
    )
    return is_verified


def contains_low_conf_keywords(record):
    """Check if record contains low confidence keywords."""
    low_conf_keywords_eu = current_app.config.get("CURATION_LOW_CONF_KEYWORDS_EU")
    record_data = (
        record.metadata["title"] + " " + record.metadata.get("description", "")
    )

    for word in low_conf_keywords_eu:
        # TODO could possibly return a number for higher conf
        if word.lower() in record_data.lower():
            return True
    return False


def contains_high_conf_keywords(record):
    """Check if record contains high confidence keywords."""
    high_conf_keywords_eu = current_app.config.get("CURATION_HIGH_CONF_KEYWORDS_EU")
    record_data = (
        record.metadata["title"] + " " + record.metadata.get("description", "")
    )

    for word in high_conf_keywords_eu:
        # TODO could possibly return a number for higher conf
        if word.lower() in record_data.lower():
            return True
    return False
