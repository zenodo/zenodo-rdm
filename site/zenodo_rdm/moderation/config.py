# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Moderation config."""

from .rules import (
    files_rule,
    links_rule,
    match_query_rule,
    text_sanitization_rule,
    verified_user_rule,
)

MODERATION_SCORES = {
    "spam_link": 8,
    "ham_link": -3,
    "excess_links": 5,
    "spam_emoji": 5,
    "spam_header_tags": 2,
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

MODERATION_SPAM_FILE_EXTS = {"jpg", "jpeg", "pdf", "png", "jfif", "docx", "webp"}
"""Frequest spam file extensions."""

# TODO: This should be moved to a table (or stored in the User model?)
MODERATION_EXEMPT_USERS = []
"""List of users exempt from moderation."""

MODERATION_RECORD_SCORE_RULES = {
    "verified_user_rule": verified_user_rule,
    "links_rule": links_rule,
    "files_rule": files_rule,
    "text_sanitization_rule": text_sanitization_rule,
    "match_query_rule": match_query_rule,
}
"""Scoring rules for record moderation."""

MODERATION_COMMUNITY_SCORE_RULES = {
    "links_rule": links_rule,
    "text_sanitization_rule": text_sanitization_rule,
    "verified_user_rule": verified_user_rule,
    "match_query_rule": match_query_rule,
}
"""Scoring rules for communtiy moderation."""

MODERATION_PERCOLATOR_INDEX_PREFIX = "moderation-queries"
"""Index Prefix for percolator index."""

MODERATION_PERCOLATOR_MAPPING = {
    "properties": {
        "query": {"type": "percolator"},
        "score": {"type": "integer"},
        "notes": {"type": "text"},
        "active": {"type": "boolean"},
    }
}
"""Properties for moderation percolator index."""
