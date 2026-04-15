# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration tests for the real ``ZENODO_LEGACY_SEARCH_MAP``.

We publish records against live Postgres + OpenSearch, then fire legacy
query strings at ``records_service.search``. The service's search options
are wired (in ``conftest.app_config``) to the production
``ZENODO_LEGACY_SEARCH_MAP``, so a regression in the real mapping — not a
local copy — will surface here.
"""

import pytest
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service as records_service
from invenio_rdm_records.records.api import RDMRecord


def _search_ids(query_str):
    """Hit the live index through the production legacy query parser."""
    hits = records_service.search(system_identity, params={"q": query_str}).to_dict()[
        "hits"
    ]["hits"]
    return sorted(h["id"] for h in hits)


def _publish(record_data, community=None):
    draft = records_service.create(system_identity, record_data)
    if community is not None:
        draft._record.parent.communities.add(community._record, default=True)
        draft._record.parent.commit()
        draft._record.commit()
        db.session.commit()
    return records_service.publish(system_identity, draft.id)


@pytest.fixture()
def published_records(running_app, minimal_record, community):
    """Publish a dissertation (in community, with DOI) and a plain book."""
    base = dict(minimal_record, files={"enabled": False})

    dissertation = dict(
        base,
        metadata=dict(
            base["metadata"],
            resource_type={"id": "publication-dissertation"},
            title="A thesis",
        ),
        pids={"doi": {"identifier": "10.1234/thesis", "provider": "external"}},
    )
    dissertation_rec = _publish(dissertation, community=community)

    book = dict(
        base,
        metadata=dict(
            base["metadata"],
            resource_type={"id": "publication-book"},
            title="A book",
        ),
    )
    book_rec = _publish(book)

    RDMRecord.index.refresh()
    return {
        "dissertation_id": dissertation_rec.id,
        "book_id": book_rec.id,
        "community_slug": community.data["slug"],
    }


def test_legacy_search_map_value_mappers(published_records):
    """End-to-end checks for the ``ZENODO_LEGACY_SEARCH_MAP`` value mappers."""
    dissertation_id = published_records["dissertation_id"]
    book_id = published_records["book_id"]
    slug = published_records["community_slug"]

    # Legacy ``publication-thesis`` still reaches the post-migration record
    # (word and phrase forms), alongside the current ``publication-dissertation``.
    assert _search_ids("resource_type.subtype:publication-thesis") == [dissertation_id]
    assert _search_ids('resource_type.subtype:"publication-thesis"') == [
        dissertation_id
    ]
    assert _search_ids("resource_type.subtype:publication-dissertation") == [
        dissertation_id
    ]
    # Non-rewritten subtypes pass through untouched.
    assert _search_ids("resource_type.subtype:publication-book") == [book_id]

    # ``10.*`` DOIs get phrase-wrapped so ``/`` isn't tokenized.
    assert _search_ids("doi:10.1234/thesis") == [dissertation_id]

    # Community slug resolves to the UUID stored on ``parent.communities.ids``.
    assert _search_ids(f"communities:{slug}") == [dissertation_id]
    # Unknown slug resolves to ``"None"`` and matches nothing.
    assert _search_ids("communities:does-not-exist") == []
