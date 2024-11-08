# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Rules for moderation."""

import re

from flask import current_app
from invenio_search import current_search_client
from invenio_search.utils import build_alias_name

from .models import LinkDomain, LinkDomainStatus
from .percolator import get_percolator_index
from .proxies import current_scores

#
# Utilities
#
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # Emoticons
    "\U0001f300-\U0001f5ff"  # Symbols & Pictographs
    "\U0001f680-\U0001f6ff"  # Transport & Map Symbols
    "\U0001f1e0-\U0001f1ff"  # Flags (iOS)
    "\U00002700-\U000027bf"  # Dingbats
    "\U000024c2-\U0001f251"  # Enclosed characters
    "]+",
    flags=re.UNICODE,
)


def extract_emojis(text):
    """Extract all emojis from text using a regex pattern."""
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


#
# Rules
#
def links_rule(identity, draft=None, record=None):
    """Calculate a moderation score based on links found in record metadata."""
    score = 0
    description_links = extract_links(str(record.metadata.get("description", "")))

    if len(description_links) > 5:
        score += current_scores.excess_links

    extracted_links = extract_links(str(record.metadata))

    for link in extracted_links:
        domain = LinkDomain.lookup_domain(link)
        if domain is None:
            continue
        if domain.status == LinkDomainStatus.BANNED:
            if domain.score is not None:
                score += domain.score
            else:
                score += current_scores.spam_link
        elif domain == LinkDomainStatus.SAFE:
            if domain.score is not None:
                score += domain.score
            else:
                score += current_scores.ham_link
    return score


def text_sanitization_rule(identity, draft=None, record=None):
    """Calculate a score based on excessive emoji and HTML tag usage in metadata text."""
    record_text = " ".join(map(str, record.metadata.values()))
    htag_count = len(re.findall(r"<h[1-9]\b[^>]*>", record_text, re.IGNORECASE))
    score = 0

    if len(extract_emojis(record_text)) > 3:
        score += current_scores.spam_emoji

    if htag_count > 4:
        score += current_scores.spam_header_tags

    return score


def verified_user_rule(identity, draft=None, record=None):
    """Adjust moderation score based on the verification status of the user."""
    is_verified = (
        getattr(record.parent, "is_verified", None)
        if hasattr(record, "parent")
        else getattr(record, "is_verified", False)
    )
    return (
        current_scores.unverified_user
        if not is_verified
        else current_scores.verified_user
    )


def files_rule(identity, draft=None, record=None):
    """Calculate score based on the number, size, and type of files associated with the record."""
    score = 0

    files_count = record.files.count
    data_size = record.files.total_bytes
    exts = {filename.split(".")[-1].lower() for filename in record.files.entries.keys()}

    max_spam_file_size = current_app.config.get("MODERATION_MAX_SPAM_FILE_SIZE")
    min_ham_file_size = current_app.config.get("MODERATION_MIN_HAM_FILE_SIZE")
    spam_exts = len(
        exts.intersection(current_app.config.get("MODERATION_SPAM_FILE_EXTS"))
    )

    if files_count <= 4 and data_size < max_spam_file_size and spam_exts > 0:
        score += current_scores.spam_files

    if files_count > 4 or data_size > min_ham_file_size:
        score += current_scores.ham_files

    return score


def match_query_rule(identity, draft=None, record=None):
    """Calculate a score based on matched percolate queries against the given document in the specified index."""
    document = record.dumps()
    percolator_index = get_percolator_index(record)
    if percolator_index:
        matched_queries = current_search_client.search(
            index=percolator_index,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"active": True}},
                            {"percolate": {"field": "query", "document": document}},
                        ]
                    }
                }
            },
        )

    score = 0

    for hit in matched_queries["hits"]["hits"]:
        query_score = hit["_source"].get("score", 0)
        score += query_score
    return score
