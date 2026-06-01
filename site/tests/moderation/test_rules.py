# SPDX-FileCopyrightText: 2024-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for moderation scoring rules."""

from datetime import datetime, timezone
from io import BytesIO

import pytest
from flask_principal import Need
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_search import current_search_client

from zenodo_rdm.moderation.models import LinkDomain, LinkDomainStatus
from zenodo_rdm.moderation.percolator import (
    create_percolator_index,
    get_percolator_index,
    index_percolate_query,
)
from zenodo_rdm.moderation.proxies import current_scores
from zenodo_rdm.moderation.rules import (
    FilesRule,
    LinksRule,
    MatchQueryRule,
    TextSanitizationRule,
    VerifiedUserRule,
    extract_emojis,
    extract_links,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        # href targets and bare URLs are both extracted, in order
        ('<a href="http://bad.ru/x">click</a>', ["http://bad.ru/x"]),
        ("see http://a.com and www.b.org", ["http://a.com", "www.b.org"]),
        ('mix <a href="http://h.com">x</a> http://bare.com', ["http://h.com", "http://bare.com"]),
        ("no links here", []),
        # repeated URLs are NOT deduplicated: each occurrence counts toward
        # the >5 excess-links threshold
        ("http://a.com http://a.com", ["http://a.com", "http://a.com"]),
    ],
)
def test_extract_links(text, expected):
    """Links are extracted from hrefs and bare URLs, without deduplication."""
    assert extract_links(text) == expected


@pytest.mark.parametrize(
    "text,expected_matches",
    [
        ("plain ascii text", 0),
        # separated emoji are distinct matches
        ("hi 😀 there 🎉 ok 🚀", 3),
        # a consecutive run counts as a single match (not 4 emoji)
        ("😀😀😀😀", 1),
    ],
)
def test_extract_emojis_counts_runs(text, expected_matches):
    """Emoji detection matches runs, which is what the >3 threshold counts."""
    assert len(extract_emojis(text)) == expected_matches


@pytest.fixture()
def spam_query(running_app, db):
    """A percolator spam query matching a distinctive title, scored as spam.

    The percolator index isn't invenio-managed, so the search fixture won't
    clean it; we wipe and recreate it per test to keep queries from piling up.
    """
    record_cls = records_service.record_cls
    index = get_percolator_index(record_cls)
    current_search_client.indices.delete(index=index, ignore=[400, 404])
    create_percolator_index(record_cls)
    index_percolate_query(
        record_cls,
        query_id="q-spam-title",
        query_string="metadata.title:Spammacious",
        active=True,
        score=8,
        notes="spammy title",
    )
    current_search_client.indices.refresh(index=index)
    yield {"score": 8, "notes": "spammy title"}
    current_search_client.indices.delete(index=index, ignore=[400, 404])


@pytest.fixture()
def spam_record_data(minimal_record):
    """Metadata-only record data whose title matches the spam query."""
    return {
        **minimal_record,
        "files": {"enabled": False},
        "metadata": {**minimal_record["metadata"], "title": "Spammacious"},
    }


def test_match_query_rule_matches_published_record(spam_query, spam_record_data):
    """A published record whose title matches a spam query is scored."""
    item = records_service.create(system_identity, spam_record_data)
    record = records_service.publish(system_identity, item.id)._record

    result = MatchQueryRule()(system_identity, record=record)

    assert result.score == spam_query["score"]
    assert [r.code for r in result.reasons] == ["matched_query"]
    reason = result.reasons[0]
    assert reason.query_id == "q-spam-title"
    assert reason.notes == spam_query["notes"]


def test_match_query_rule_matches_draft(spam_query, spam_record_data):
    """A draft is percolated against the records index (no drafts index exists).

    Regression for re-evaluating moderation on a draft: the rule must drop the
    draft-only fields the strict records mapping rejects and still match.
    """
    draft = records_service.create(system_identity, spam_record_data)._record
    assert draft.is_draft  # guard: we are exercising the draft path

    result = MatchQueryRule()(system_identity, draft=draft)

    assert result.score == spam_query["score"]
    assert [r.code for r in result.reasons] == ["matched_query"]


def test_match_query_rule_no_match(spam_query, minimal_record):
    """A record that matches no spam query scores zero with no reasons."""
    data = {**minimal_record, "files": {"enabled": False}}
    item = records_service.create(system_identity, data)
    record = records_service.publish(system_identity, item.id)._record

    result = MatchQueryRule()(system_identity, record=record)

    assert result.score == 0
    assert result.reasons == []


@pytest.fixture()
def banned_domain(db):
    """A banned link domain."""
    domain = LinkDomain.create("spam.example", LinkDomainStatus.BANNED)
    db.session.commit()
    return domain


def test_links_rule_flags_excess_links_and_banned_domains(
    running_app, db, banned_domain, minimal_record
):
    """A description full of links to a banned domain is scored as spam."""
    links = " ".join(f"http://spam.example/{i}" for i in range(6))
    data = {
        **minimal_record,
        "files": {"enabled": False},
        "metadata": {**minimal_record["metadata"], "description": f"Visit {links}"},
    }
    item = records_service.create(system_identity, data)
    record = records_service.publish(system_identity, item.id)._record

    result = LinksRule()(system_identity, record=record)

    excess = [r for r in result.reasons if r.code == "excess_description_links"]
    assert len(excess) == 1
    assert excess[0].score == current_scores.excess_links  # 6 links > 5

    domains = [r for r in result.reasons if r.code == "link_domain"]
    assert domains
    assert all(r.status == "spam" for r in domains)
    assert all(r.score == current_scores.spam_link for r in domains)


def test_text_sanitization_rule_flags_excess_emoji(running_app, db, minimal_record):
    """A description with more than three emoji is flagged."""
    data = {
        **minimal_record,
        "files": {"enabled": False},
        "metadata": {**minimal_record["metadata"], "description": "Amazing 🎉🎉🎉🎉 work"},
    }
    item = records_service.create(system_identity, data)
    record = records_service.publish(system_identity, item.id)._record

    result = TextSanitizationRule()(system_identity, record=record)

    by_code = {r.code: r for r in result.reasons}
    assert by_code["excess_emoji"].count >= 4
    assert by_code["excess_emoji"].score == current_scores.spam_emoji
    assert by_code["excess_header_tags"].score == 0


def _make_owner(UserFixture, app, db, email, verified_at):
    """Create a user with a given verification timestamp."""
    u = UserFixture(email=email, password="123456")
    u.create(app, db)
    u.user.verified_at = verified_at
    db.session.commit()
    # Resolving is_verified in tests needs an authenticated identity.
    u.identity.provides.add(Need(method="system_role", value="authenticated_user"))
    return u


@pytest.fixture()
def unverified_owner(UserFixture, app, db):
    """A record owner whose account is not verified."""
    return _make_owner(UserFixture, app, db, "unverified@test.org", None)


@pytest.fixture()
def verified_owner(UserFixture, app, db):
    """A record owner whose account is verified."""
    return _make_owner(
        UserFixture, app, db, "verified@test.org", datetime.now(timezone.utc)
    )


def test_verified_user_rule_unverified_owner(
    running_app, db, unverified_owner, minimal_record
):
    """An unverified owner adds the unverified-user score."""
    data = {**minimal_record, "files": {"enabled": False}}
    item = records_service.create(unverified_owner.identity, data)
    record = records_service.publish(unverified_owner.identity, item.id)._record

    reason = VerifiedUserRule()(unverified_owner.identity, record=record).reasons[0]

    assert reason.verified is False
    assert reason.score == current_scores.unverified_user


def test_verified_user_rule_verified_owner(
    running_app, db, verified_owner, minimal_record
):
    """A verified owner subtracts via the verified-user score."""
    data = {**minimal_record, "files": {"enabled": False}}
    item = records_service.create(verified_owner.identity, data)
    record = records_service.publish(verified_owner.identity, item.id)._record

    reason = VerifiedUserRule()(verified_owner.identity, record=record).reasons[0]

    assert reason.verified is True
    assert reason.score == current_scores.verified_user


def _publish_with_files(identity, data, files):
    """Create a draft, upload files, and publish it."""
    data = {**data, "files": {"enabled": True}}
    draft = records_service.create(identity, data)
    recid = draft.id
    records_service.draft_files.init_files(
        identity, recid, [{"key": key} for key, _ in files]
    )
    for key, content in files:
        records_service.draft_files.set_file_content(
            identity, recid, key, BytesIO(content)
        )
        records_service.draft_files.commit_file(identity, recid, key)
    return records_service.publish(identity, recid)._record


def test_files_rule_flags_spam_files(running_app, db, minimal_record):
    """A few small files with a spam extension add the spam-files score."""
    record = _publish_with_files(system_identity, minimal_record, [("malware.pdf", b"x" * 10)])

    result = FilesRule()(system_identity, record=record)

    assert any(r.code == "file_stats" for r in result.reasons)
    spam = [r for r in result.reasons if r.code == "spam_files"]
    assert len(spam) == 1
    assert spam[0].score == current_scores.spam_files
    assert "pdf" in spam[0].extensions


def test_files_rule_flags_ham_files(running_app, db, minimal_record):
    """Many files indicate a genuine record and add the ham-files score."""
    files = [(f"data{i}.txt", b"content") for i in range(5)]
    record = _publish_with_files(system_identity, minimal_record, files)

    result = FilesRule()(system_identity, record=record)

    ham = [r for r in result.reasons if r.code == "ham_files"]
    assert len(ham) == 1
    assert ham[0].score == current_scores.ham_files
    assert not [r for r in result.reasons if r.code == "spam_files"]
