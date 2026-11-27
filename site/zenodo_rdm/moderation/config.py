# SPDX-FileCopyrightText: 2024-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Moderation config."""

from .rules import (
    FileRule,
    LinkRule,
    MatchQueryRule,
    MetadataSpamIndicatorsRule,
    OwnerVerifiedRule,
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
    "owner_verified_rule": OwnerVerifiedRule(),
    "link_rule": LinkRule(),
    "file_rule": FileRule(),
    "metadata_spam_indicators_rule": MetadataSpamIndicatorsRule(),
    "match_query_rule": MatchQueryRule(),
}
"""Scoring rules for record moderation."""

MODERATION_COMMUNITY_SCORE_RULES = {
    "link_rule": LinkRule(),
    "metadata_spam_indicators_rule": MetadataSpamIndicatorsRule(),
    "owner_verified_rule": OwnerVerifiedRule(),
    "match_query_rule": MatchQueryRule(),
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
