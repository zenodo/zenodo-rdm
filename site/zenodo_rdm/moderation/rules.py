# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Rules for moderation."""

import re
from urllib.parse import urlparse

from flask import current_app

from zenodo_rdm.moderation.proxies import current_domain_tree

# Moderation Scores
SPAM_LINK_SCORE = 8
HAM_LINK_SCORE = -3
EXCESS_LINKS_SCORE = 5
SPAM_EMOJI_SCORE = 5
SPAM_FILES_SCORE = 2
HAM_FILES_SCORE = -5
UNVERIFIED_USER_SCORE = 10
VERIFIED_USER_SCORE = -10


# Utility Functions


def extract_emojis(text):
    """Extract all emojis from text using a regex pattern."""
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        "\U00002700-\U000027BF"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+",
        flags=re.UNICODE,
    )
    return EMOJI_PATTERN.findall(text)


def extract_links(text):
    """Extract unique URLs from text using regex."""
    url_pattern = re.compile(
        r'href=["\']?([^"\'>]+)|\b(https?://[^\s\'"<>,]+|www\.[^\s\'"<>,]+)',
    )

    links = []
    for match in url_pattern.findall(text):
        for url in match:
            if url:
                links.append(url)

    return links


def extract_domain(url):
    """Extract and reverse domain parts from a given URL."""
    pattern = r"^(?:https?://)?(?:www\.)?([^/]+)"
    match = re.search(pattern, url)
    if match:
        domain = match.group(1)
        domain_parts = domain.split(".")
        return domain_parts[::-1]
    return None


# Moderation Rule Functions


def links_rule(identity, draft=None, record=None):
    """Calculate a moderation score based on links found in record metadata."""
    score = 0
    description_links = extract_links(str(record.metadata.get("description", "")))

    if len(description_links) > 5:
        score += EXCESS_LINKS_SCORE

    extracted_links = extract_links(str(record.metadata))

    for link in extracted_links:
        domain_parts = extract_domain(link)
        status = current_domain_tree.get_status(domain_parts)
        if status == "banned":
            score += SPAM_LINK_SCORE
        elif status == "safe":
            score += HAM_LINK_SCORE
    return score


def text_sanitization_rule(identity, draft=None, record=None):
    """Calculate a score for excessive emoji usage in metadata text."""
    record_text = " ".join(map(str, record.metadata.values()))
    return SPAM_EMOJI_SCORE if len(extract_emojis(record_text)) > 3 else 0


def verified_user_rule(identity, draft=None, record=None):
    """Adjust moderation score based on the verification status of the user."""
    is_verified = (
        getattr(record.parent, "is_verified", None)
        if hasattr(record, "parent")
        else getattr(record, "is_verified", False)
    )
    return UNVERIFIED_USER_SCORE if not is_verified else VERIFIED_USER_SCORE


def files_rule(identity, draft=None, record=None):
    """Calculate score based on the number, size, and type of files associated with the record."""
    score = 0
    files_count = record.files.count
    file_size_threshold = current_app.config.get("RDM_CONTENT_MODERATION_FILE_SIZE")
    data_size = record.files.total_bytes
    exts = {filename.split(".")[-1].lower() for filename in record.files.entries.keys()}

    if (
        files_count == 1
        and data_size < file_size_threshold
        and len(exts.intersection(current_app.config.get("SPAM_FILE_EXTS"))) > 0
    ):
        score += SPAM_FILES_SCORE

    if files_count > 3 or data_size > file_size_threshold:
        score += HAM_FILES_SCORE

    return score
