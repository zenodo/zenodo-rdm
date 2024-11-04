# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Moderation config."""

from .rules import links_rule, verified_user_rule, files_rule, text_sanitization_rule

MODERATION_BANNED_LINK_DOMAINS = []
"""Banned domains for links."""

MODERATION_SAFE_LINK_DOMAINS = []
"""Safe domains for links."""

MODERATION_SCORES = {
    "ham_link": -3,
    "excess_links": 5,
    "spam_emoji": 5,
    "spam_files": 2,
    "ham_files": -5,
    "unverified_user": 10,
    "verified_user": -10,
    "spam_threshold": 10,
    "ham_threshold": 0,
}
"""Moderation score values for rules."""

MODERATION_APPLY_ACTIONS = False
"""Apply actions based on moderation scores."""

MODERATION_MAX_SPAM_FILE_SIZE = 5_000_000  # 5MB
"""Maximum file size for spam files."""
MODERATION_MIN_HAM_FILE_SIZE = 15_000_000  # 15MB
"""Minimum file size for ham files."""

MODERATION_SPAM_FILE_EXTS = {'jpg', 'jpeg', 'pdf', 'png', 'jfif'}
"""Frequest spam file extensions."""

MODERATION_RECORD_SCORE_RULES = [
    verified_user_rule,
    links_rule,
    files_rule,
    text_sanitization_rule
]
"""Scoring rules for record moderation."""

MODERATION_COMMUNITY_SCORE_RULES = [
    links_rule,
    text_sanitization_rule,
    verified_user_rule,
]
"""Scoring rules for communtiy moderation."""
