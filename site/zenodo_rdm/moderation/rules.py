# SPDX-FileCopyrightText: 2024-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rules for moderation.

Each rule's reason types are nested in the rule that produces them, so a rule
reads as one self-contained unit. See ``base.py`` for the ``Rule``/``Reason``/
``RuleResult`` contract these build on.
"""

import re
from dataclasses import dataclass, field

from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_search import current_search_client

from .base import Reason, Rule, RuleResult
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
    "]",
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
class LinksRule(Rule):
    """Score based on links found in record metadata."""

    @dataclass(frozen=True)
    class Excess(Reason):
        """Number of links found in the description."""

        code: str = field(default="excess_description_links", init=False)
        count: int = 0

    @dataclass(frozen=True)
    class Domain(Reason):
        """A known domain (safe or spam) linked from the metadata."""

        code: str = field(default="link_domain", init=False)
        domain: str = ""
        status: str = ""

    def evaluate(self, identity, record) -> RuleResult:
        """Score the record's links."""
        reasons = []

        description_links = extract_links(str(record.metadata.get("description", "")))
        reasons.append(
            self.Excess(
                score=current_scores.excess_links if len(description_links) > 5 else 0,
                label=f"{len(description_links)} links in description",
                count=len(description_links),
            )
        )

        for link in extract_links(str(record.metadata)):
            domain = LinkDomain.lookup_domain(link)
            if domain is None:
                continue
            is_safe = domain.status == LinkDomainStatus.SAFE
            default = current_scores.ham_link if is_safe else current_scores.spam_link
            reasons.append(
                self.Domain(
                    score=domain.score if domain.score is not None else default,
                    label=f"link to {'safe' if is_safe else 'spam'} domain {domain.domain}",
                    domain=domain.domain,
                    status="safe" if is_safe else "spam",
                )
            )

        return RuleResult(reasons=reasons)


class TextSanitizationRule(Rule):
    """Score based on excessive emoji and HTML tag usage in metadata text."""

    @dataclass(frozen=True)
    class Emoji(Reason):
        """Count of emoji found in the metadata text."""

        code: str = field(default="excess_emoji", init=False)
        count: int = 0

    @dataclass(frozen=True)
    class HeaderTags(Reason):
        """Count of HTML header tags found in the metadata text."""

        code: str = field(default="excess_header_tags", init=False)
        count: int = 0

    def evaluate(self, identity, record) -> RuleResult:
        """Score the record's metadata text."""
        record_text = " ".join(map(str, record.metadata.values()))
        emoji_count = len(extract_emojis(record_text))
        htag_count = len(re.findall(r"<h[1-9]\b[^>]*>", record_text, re.IGNORECASE))

        return RuleResult(
            reasons=[
                self.Emoji(
                    score=current_scores.spam_emoji if emoji_count > 3 else 0,
                    label=f"{emoji_count} emoji in metadata",
                    count=emoji_count,
                ),
                self.HeaderTags(
                    score=current_scores.spam_header_tags if htag_count > 4 else 0,
                    label=f"{htag_count} header tags in metadata",
                    count=htag_count,
                ),
            ]
        )


class VerifiedUserRule(Rule):
    """Adjust score based on the verification status of the owner."""

    @dataclass(frozen=True)
    class Verification(Reason):
        """Verification status of the record/community owner."""

        code: str = field(default="user_verification", init=False)
        verified: bool = False

    def evaluate(self, identity, record) -> RuleResult:
        """Score the owner's verification status."""
        is_verified = (
            getattr(record.parent, "is_verified", None)
            if hasattr(record, "parent")
            else getattr(record, "is_verified", False)
        )
        return RuleResult(
            reasons=[
                self.Verification(
                    score=current_scores.verified_user
                    if is_verified
                    else current_scores.unverified_user,
                    label=f"owner is {'verified' if is_verified else 'unverified'}",
                    verified=bool(is_verified),
                )
            ]
        )


class FilesRule(Rule):
    """Score based on the number, size, and type of files on the record."""

    @dataclass(frozen=True)
    class Stats(Reason):
        """Informational snapshot of the record's files (always score 0)."""

        code: str = field(default="file_stats", init=False)
        files_count: int = 0
        total_bytes: int = 0
        extensions: tuple = ()

    @dataclass(frozen=True)
    class Spam(Reason):
        """Few small files with a spam-associated extension."""

        code: str = field(default="spam_files", init=False)
        extensions: tuple = ()

    @dataclass(frozen=True)
    class Ham(Reason):
        """Many files or a large payload, indicative of a genuine record."""

        code: str = field(default="ham_files", init=False)

    def evaluate(self, identity, record) -> RuleResult:
        """Score the record's files."""
        files_count = record.files.count
        data_size = record.files.total_bytes
        exts = {fn.split(".")[-1].lower() for fn in record.files.entries.keys()}

        max_spam_file_size = current_app.config.get("MODERATION_MAX_SPAM_FILE_SIZE")
        min_ham_file_size = current_app.config.get("MODERATION_MIN_HAM_FILE_SIZE")
        spam_exts = exts.intersection(
            current_app.config.get("MODERATION_SPAM_FILE_EXTS")
        )

        reasons = [
            self.Stats(
                score=0,
                label=f"{files_count} files, {data_size} bytes",
                files_count=files_count,
                total_bytes=data_size,
                extensions=tuple(sorted(exts)),
            )
        ]

        if files_count <= 4 and data_size < max_spam_file_size and spam_exts:
            reasons.append(
                self.Spam(
                    score=current_scores.spam_files,
                    label=f"few small files with spam extensions {sorted(spam_exts)}",
                    extensions=tuple(sorted(spam_exts)),
                )
            )

        if files_count > 4 or data_size > min_ham_file_size:
            reasons.append(
                self.Ham(
                    score=current_scores.ham_files,
                    label="many files or large payload",
                )
            )

        return RuleResult(reasons=reasons)


class MatchQueryRule(Rule):
    """Score based on matched percolate queries against the document."""

    @dataclass(frozen=True)
    class Match(Reason):
        """A percolator spam query that matched the document."""

        code: str = field(default="matched_query", init=False)
        query_id: int = 0
        notes: str = ""

    def evaluate(self, identity, record) -> RuleResult:
        """Score the record against the percolator spam queries."""
        document = record.dumps()
        # Drafts have no percolator index of their own; percolate against the
        # published-records index and drop draft-only fields the strict mapping rejects.
        index_cls = record
        if getattr(record, "is_draft", False):
            document.pop("expires_at", None)
            document.pop("fork_version_id", None)
            index_cls = current_rdm_records_service.record_cls
        percolator_index = get_percolator_index(index_cls)

        reasons = []
        if percolator_index:
            matched_queries = current_search_client.search(
                index=percolator_index,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"active": True}},
                                {
                                    "percolate": {
                                        "field": "query",
                                        "document": document,
                                    }
                                },
                            ]
                        }
                    }
                },
            )
            for hit in matched_queries["hits"]["hits"]:
                source = hit["_source"]
                notes = source.get("notes") or ""
                reasons.append(
                    self.Match(
                        score=source.get("score", 0),
                        label=f"matched spam query #{source.get('id')}"
                        + (f": {notes}" if notes else ""),
                        query_id=source.get("id"),
                        notes=notes,
                    )
                )

        return RuleResult(reasons=reasons)
