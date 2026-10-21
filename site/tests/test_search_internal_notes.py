# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test that internal notes cannot be searched by regular users."""

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import (
    current_community_records_service as community_records_service,
)
from invenio_rdm_records.proxies import current_rdm_records_service as records_service

MARKER = "zzsecretmarker"

# Queries that select records by the content (or presence) of internal notes.
NOTE_QUERIES = [
    f"internal_notes.note:{MARKER}",
    f'internal_notes.note:"{MARKER}"',
    "internal_notes.note:zzsecret*",
    "internal_notes.id:*",
    "internal_notes.added_by.user:system",
    "internal_notes.timestamp:[* TO *]",
    "_exists_:internal_notes",
    "_exists_:internal_notes.note",
    "_exists_:internal*",
    f"internal_notes.\\*:{MARKER}",
    f"\\*.note:{MARKER}",
    f"\\*:{MARKER}",
    f"metadata.title:story AND internal_notes.note:{MARKER}",
]


@pytest.fixture()
def api_url(test_app):
    """REST API base URL."""
    return test_app.config["SITE_API_URL"]


@pytest.fixture()
def noted_records(publish_record, minimal_record, community):
    """Publish two community records, only one of them with an internal note."""
    base = dict(minimal_record, files={"enabled": False})
    noted = publish_record(
        dict(base, internal_notes=[{"note": f"Flagged as {MARKER}"}]),
        community=community,
    )
    plain = publish_record(base, community=community)
    assert noted._record["internal_notes"][0]["note"] == f"Flagged as {MARKER}"
    return {"noted": noted.id, "plain": plain.id, "community": community.id}


@pytest.fixture()
def noted_draft(running_app, minimal_record, uploader):
    """Create a draft owned by the uploader with an internal note added by the system."""
    data = dict(minimal_record, files={"enabled": False})
    draft = records_service.create(uploader.identity, data)
    draft = records_service.update_draft(
        system_identity,
        draft.id,
        dict(data, internal_notes=[{"note": f"Flagged as {MARKER}"}]),
    )
    records_service.draft_cls.index.refresh()
    return draft.id


def _scoped(query, *ids):
    """Restrict a query to the given records, so other test data cannot hide hits."""
    return f"({query}) AND id:({' OR '.join(ids)})"


def _hit_ids(result):
    return {h["id"] for h in result.to_dict()["hits"]["hits"]}


def _search_records(identity, query):
    return _hit_ids(records_service.search(identity, params={"q": query}))


def _search_community_records(identity, query, community_id):
    return _hit_ids(
        community_records_service.search(
            identity, community_id=community_id, params={"q": query}
        )
    )


@pytest.mark.parametrize("query", NOTE_QUERIES)
def test_records_search_cannot_query_internal_notes(
    client, api_url, uploader, noted_records, query
):
    """Anonymous and authenticated users cannot match records by internal notes."""
    query = _scoped(query, noted_records["noted"], noted_records["plain"])
    # Anonymous REST API search
    res = client.get(f"{api_url}/records", query_string={"q": query})
    assert res.status_code == 200
    assert noted_records["noted"] not in {h["id"] for h in res.json["hits"]["hits"]}

    # Authenticated user
    assert noted_records["noted"] not in _search_records(uploader.identity, query)


@pytest.mark.parametrize("query", NOTE_QUERIES)
def test_community_records_search_cannot_query_internal_notes(
    client, api_url, uploader, noted_records, query
):
    """Community records search cannot match records by internal notes."""
    community_id = noted_records["community"]
    query = _scoped(query, noted_records["noted"], noted_records["plain"])
    res = client.get(
        f"{api_url}/communities/{community_id}/records", query_string={"q": query}
    )
    assert res.status_code == 200
    assert noted_records["noted"] not in {h["id"] for h in res.json["hits"]["hits"]}

    hits = _search_community_records(uploader.identity, query, community_id)
    assert noted_records["noted"] not in hits


@pytest.mark.parametrize("query", NOTE_QUERIES)
def test_versions_search_cannot_query_internal_notes(
    client, api_url, uploader, noted_records, query
):
    """Record versions search cannot match records by internal notes."""
    recid = noted_records["noted"]
    res = client.get(f"{api_url}/records/{recid}/versions", query_string={"q": query})
    assert res.status_code == 200
    assert recid not in {h["id"] for h in res.json["hits"]["hits"]}

    hits = _hit_ids(
        records_service.search_versions(uploader.identity, recid, params={"q": query})
    )
    assert recid not in hits


@pytest.mark.parametrize("query", NOTE_QUERIES)
def test_drafts_search_cannot_query_internal_notes(uploader, noted_draft, query):
    """The draft owner cannot match their own drafts by internal notes."""
    query = _scoped(query, noted_draft)
    hits = _hit_ids(
        records_service.search_drafts(uploader.identity, params={"q": query})
    )
    assert noted_draft not in hits


def test_negated_note_query_does_not_distinguish_records(uploader, noted_records):
    """Negating a note query must not single out records with notes."""
    query = _scoped(
        "NOT _exists_:internal_notes", noted_records["noted"], noted_records["plain"]
    )
    hits = _search_records(uploader.identity, query)
    assert (noted_records["noted"] in hits) == (noted_records["plain"] in hits)


def test_free_text_does_not_match_internal_notes(uploader, noted_records):
    """Plain free-text search does not look into internal notes."""
    query = _scoped(MARKER, noted_records["noted"])
    assert noted_records["noted"] not in _search_records(uploader.identity, query)


def test_drafts_free_text_does_not_match_internal_notes(uploader, noted_draft):
    """Plain free-text search on drafts does not look into internal notes."""
    query = _scoped(MARKER, noted_draft)
    hits = _hit_ids(
        records_service.search_drafts(uploader.identity, params={"q": query})
    )
    assert noted_draft not in hits

    # Metadata default fields are still searched
    query = _scoped("Romans", noted_draft)
    hits = _hit_ids(
        records_service.search_drafts(uploader.identity, params={"q": query})
    )
    assert noted_draft in hits


@pytest.mark.parametrize(
    "query",
    [
        f"internal_notes.note:{MARKER}",
        "internal_notes.added_by.user:system",
        "_exists_:internal_notes",
    ],
)
def test_system_can_query_internal_notes(noted_records, query):
    """The system process can still search by internal notes."""
    query = _scoped(query, noted_records["noted"], noted_records["plain"])
    hits = _search_records(system_identity, query)
    assert noted_records["noted"] in hits
    assert noted_records["plain"] not in hits
