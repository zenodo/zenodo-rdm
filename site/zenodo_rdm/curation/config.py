# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Moderation config."""

from .rules import (
    award_acronym_in_description,
    award_acronym_in_title,
    test_phrases_in_record,
)

CURATION_EU_RULES = {
    "award_acronym_in_title": award_acronym_in_title,
    "award_acronym_in_description": award_acronym_in_description,
    "test_phrases_in_record": test_phrases_in_record,
}
"""Rules to run for EU Curation."""

CURATION_ENABLE_EU_CURATOR = False
"""Controls whether to dry run EU Curation."""
