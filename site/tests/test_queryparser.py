# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration tests for search query transforms."""

import pytest
from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service as records_service


@pytest.fixture()
def published_records(publish_record, minimal_record, community):
    """Publish a dissertation and a book, bidirectionally related."""
    base = dict(minimal_record, files={"enabled": False})

    dissertation = dict(
        base,
        metadata=dict(
            base["metadata"],
            resource_type={"id": "publication-dissertation"},
            title="A thesis",
            related_identifiers=[
                {
                    "identifier": "10.1234/book",
                    "relation_type": {"id": "iscitedby"},
                    "scheme": "doi",
                    "resource_type": {"id": "publication-book"},
                },
            ],
        ),
        pids={"doi": {"identifier": "10.1234/thesis", "provider": "external"}},
    )
    dissertation_rec = publish_record(dissertation, community=community)

    book = dict(
        base,
        metadata=dict(
            base["metadata"],
            resource_type={"id": "publication-book"},
            title="A book",
            related_identifiers=[
                {
                    "identifier": "10.1234/thesis",
                    "relation_type": {"id": "cites"},
                    "scheme": "doi",
                    "resource_type": {"id": "publication-dissertation"},
                },
            ],
        ),
        pids={"doi": {"identifier": "10.1234/book", "provider": "external"}},
    )
    book_rec = publish_record(book)

    return {
        "dissertation_id": dissertation_rec.id,
        "book_id": book_rec.id,
        "community_slug": community.data["slug"],
    }


def test_search_map_value_mappers(published_records):
    """End-to-end checks for the ``ZENODO_LEGACY_SEARCH_MAP`` value mappers."""
    dissertation_id = published_records["dissertation_id"]
    book_id = published_records["book_id"]
    slug = published_records["community_slug"]

    def _search_ids(query_str):
        res = records_service.search(system_identity, params={"q": query_str}).to_dict()
        return sorted(h["id"] for h in res["hits"]["hits"])

    for query, expected in [
        # Current thesis resource type (publication-dissertation) match the record
        ("resource_type.subtype:publication-dissertation", [dissertation_id]),
        ('resource_type.subtype:"publication-dissertation"', [dissertation_id]),
        ("metadata.resource_type.id:publication-dissertation", [dissertation_id]),
        ('metadata.resource_type.id:"publication-dissertation"', [dissertation_id]),
        (
            "metadata.resource_type.props.subtype:publication-dissertation",
            [dissertation_id],
        ),
        # Rewritten `publication-thesis` values match the record
        ("resource_type.subtype:publication-thesis", [dissertation_id]),
        ('resource_type.subtype:"publication-thesis"', [dissertation_id]),
        ("metadata.resource_type.id:publication-thesis", [dissertation_id]),
        ('metadata.resource_type.id:"publication-thesis"', [dissertation_id]),
        ("metadata.resource_type.props.subtype:publication-thesis", [dissertation_id]),
        ("metadata.related_identifiers.resource_type.id:publication-thesis", [book_id]),
        # Non-rewritten values pass through untouched
        ("resource_type.subtype:publication-book", [book_id]),
        ('resource_type.subtype:"publication-book"', [book_id]),
        ("metadata.resource_type.id:publication-book", [book_id]),
        ('metadata.resource_type.id:"publication-book"', [book_id]),
        ("metadata.resource_type.props.subtype:publication-book", [book_id]),
        (
            "metadata.related_identifiers.resource_type.id:publication-book",
            [dissertation_id],
        ),
        # `10.*` DOIs get phrase-wrapped so `/` isn't tokenized.
        ('doi:"10.1234/thesis"', [dissertation_id]),
        # Community slug resolves to the UUID stored in `parent.communities.ids`.
        (f"communities:{slug}", [dissertation_id]),
        (f'communities:"{slug}"', [dissertation_id]),
        # Unknown slug resolves to `"None"` and matches nothing.
        ('communities:"does-not-exist"', []),
    ]:
        assert _search_ids(query) == expected, (
            f"Query {query!r} expected {expected} but got {_search_ids(query)}"
        )
