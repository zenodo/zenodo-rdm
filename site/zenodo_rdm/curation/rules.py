# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Rules for curation."""

import arrow
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from invenio_rdm_records.requests import CommunityInclusion, CommunitySubmission
from invenio_records_resources.proxies import current_service_registry
from invenio_requests.proxies import current_requests_service
from invenio_search.engine import dsl


def award_acronym_in_description(record):
    """Check if EU award name in record description."""
    award_service = current_service_registry.get("awards")
    description = record.metadata.get("description")
    if not description:
        return False

    funding = record.metadata.get("funding", [])
    for f in funding:
        if f["funder"].get("id") == "00k4n6c32":
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

    funding = record.metadata.get("funding", [])
    for f in funding:
        if f["funder"].get("id") == "00k4n6c32":
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

    funding = record.metadata.get("funding", [])
    for f in funding:
        if f["funder"].get("id") == "00k4n6c32":
            if award_id := f.get("award", {}).get("id"):
                award = award_service.record_cls.pid.resolve(award_id)
                if award.get("start_date") and (
                    record.created.timestamp()
                    < arrow.get(award.get("start_date")).datetime.timestamp()
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


def additional_desc_contains_high_conf_keywords(record):
    """Check if additional description contains high confidence keywords."""
    high_conf_keywords_eu = current_app.config.get("CURATION_HIGH_CONF_KEYWORDS_EU")
    additional_descriptions = record.metadata.get("additional_descriptions", [])
    record_data = " ".join([x.get("description", "") for x in additional_descriptions])

    for word in high_conf_keywords_eu:
        # TODO could possibly return a number for higher conf
        if word.lower() in record_data.lower():
            return True
    return False


def additional_desc_contains_low_conf_keywords(record):
    """Check if additional description contains low confidence keywords."""
    low_conf_keywords_eu = current_app.config.get("CURATION_LOW_CONF_KEYWORDS_EU")
    additional_descriptions = record.metadata.get("additional_descriptions", [])
    record_data = " ".join([x.get("description", "") for x in additional_descriptions])

    for word in low_conf_keywords_eu:
        # TODO could possibly return a number for higher conf
        if word.lower() in record_data.lower():
            return True
    return False


def award_acronym_in_additional_description(record):
    """Check if EU award name in record additional description."""
    award_service = current_service_registry.get("awards")
    additional_descriptions = record.metadata.get("additional_descriptions", [])
    record_data = " ".join([x.get("description", "") for x in additional_descriptions])

    funding = record.metadata.get("funding", [])
    for f in funding:
        if f["funder"].get("id") == "00k4n6c32":
            if award_id := f.get("award", {}).get("id"):
                award = award_service.record_cls.pid.resolve(award_id)
                if award.get("acronym") and (
                    award.get("acronym").lower() in record_data.lower()
                ):
                    return True
    return False


def eu_community_declined_request(record):
    """Check if record was rejected from EU community."""
    community_requests = dsl.Q(
        "bool",
        must=[
            dsl.Q(
                "term",
                **{"receiver.community": current_app.config.get("EU_COMMUNITY_UUID")},
            ),
            dsl.Q("term", **{"topic.record": record.pid.pid_value}),
        ],
    )
    request_types = dsl.Q(
        "bool",
        should=[
            dsl.Q("term", **{"type": CommunityInclusion.type_id}),
            dsl.Q("term", **{"type": CommunitySubmission.type_id}),
        ],
        minimum_should_match=1,
    )
    finalq = community_requests & request_types
    results = current_requests_service.search(system_identity, extra_filter=finalq)

    for result in results:
        if result["is_closed"] and result["status"] == "declined":
            return True
        if result["is_open"] and not result["is_expired"]:
            return True
    return False


def eu_subcommunity_declined_request(record):
    """Check if record was rejected from EU sub community."""
    record_requests = dsl.Q(
        "bool",
        must=[
            dsl.Q("term", **{"topic.record": record.pid.pid_value}),
            dsl.Q("term", **{"is_open": False}),
        ],
    )
    request_types = dsl.Q(
        "bool",
        should=[
            dsl.Q("term", **{"type": CommunityInclusion.type_id}),
            dsl.Q("term", **{"type": CommunitySubmission.type_id}),
        ],
        minimum_should_match=1,
    )
    finalq = record_requests & request_types
    results = current_requests_service.search(system_identity, extra_filter=finalq)

    for result in results:
        receiver = current_communities.service.record_cls.pid.resolve(
            result["receiver"]["community"]
        )
        if receiver.parent and str(receiver.parent.id) == current_app.config.get(
            "EU_COMMUNITY_UUID"
        ):
            if result["status"] == "declined":
                return True
    return False


def community_name_award_acronym(record):
    """Check if award acronym in community name."""
    comm_text = ""
    for comm in record.parent.communities:
        comm_text += comm.metadata.get("title", "")
        comm_text += comm.metadata.get("page", "")

    if comm_text:
        award_service = current_service_registry.get("awards")
        funding = record.metadata.get("funding", [])
        for f in funding:
            if f["funder"].get("id") == "00k4n6c32":
                if award_id := f.get("award", {}).get("id"):
                    award = award_service.record_cls.pid.resolve(award_id)
                    if award.get("acronym") and (
                        award.get("acronym").lower() in comm_text.lower()
                    ):
                        return True
    return False
