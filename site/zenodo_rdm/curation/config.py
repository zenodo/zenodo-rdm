# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Moderation config."""

from .rules import (
    additional_desc_contains_high_conf_keywords,
    additional_desc_contains_low_conf_keywords,
    award_acronym_in_additional_description,
    award_acronym_in_description,
    award_acronym_in_title,
    contains_high_conf_keywords,
    contains_low_conf_keywords,
    published_before_award_start,
    test_phrases_in_record,
    user_verified,
)

CURATION_EU_RULES = {
    "award_acronym_in_title": award_acronym_in_title,
    "award_acronym_in_description": award_acronym_in_description,
    "test_phrases_in_record": test_phrases_in_record,
    "published_before_award_start": published_before_award_start,
    "user_verified": user_verified,
    "contains_low_conf_keywords": contains_low_conf_keywords,
    "contains_high_conf_keywords": contains_high_conf_keywords,
    "additional_desc_contains_low_conf_keywords": additional_desc_contains_low_conf_keywords,
    "additional_desc_contains_high_conf_keywords": additional_desc_contains_high_conf_keywords,
    "award_acronym_in_additional_description": award_acronym_in_additional_description,
}
"""Rules to run for EU Curation."""

CURATION_SCORES = {
    "award_acronym_in_title": 0,
    "award_acronym_in_description": 0,
    "test_phrases_in_record": False,
    "published_before_award_start": False,
    "user_verified": 0,
    "contains_low_conf_keywords": 0,
    "contains_high_conf_keywords": 0,
    "additional_desc_contains_low_conf_keywords": 0,
    "additional_desc_contains_high_conf_keywords": 0,
    "award_acronym_in_additional_description": 0,
}
"""Rule scores for EU Curation."""


CURATION_THRESHOLDS = {"EU_RECORDS_CURATION": 100}
"""Threshold values for curators/rules."""


CURATION_ENABLE_EU_CURATOR = False
"""Controls whether to dry run EU Curation."""

CURATION_LOW_CONF_KEYWORDS_EU = []
"""Low confidence keywords for EU records."""

CURATION_HIGH_CONF_KEYWORDS_EU = []
"""High confidence keywords for EU records."""

CURATION_TEST_PHRASES = []
"""Test record phrases."""
