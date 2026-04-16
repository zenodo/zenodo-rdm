# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Equivalence test for scroll-scan and PIT-scan exporter paths.

Publishes a handful of records — some inside a community, some outside —
against live Postgres + OpenSearch, then asserts that ``_scan_records``
returns the same set of record IDs whether it goes through the scroll API
or the Point-in-Time API.
"""

import pytest
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_rdm_records.records.api import RDMRecord

from zenodo_rdm.exporter.pit import pit_scan
from zenodo_rdm.exporter.tasks import _scan_records


def _publish(record_data, community=None):
    draft = service.create(system_identity, record_data)
    if community is not None:
        draft._record.parent.communities.add(community._record, default=True)
        draft._record.parent.commit()
        draft._record.commit()
        db.session.commit()
    return service.publish(system_identity, draft.id)


@pytest.fixture()
def published(running_app, minimal_record, community):
    """Publish three records: two in a community, one outside."""
    base = dict(minimal_record, files={"enabled": False})

    def with_title(title):
        return dict(base, metadata=dict(base["metadata"], title=title))

    in_a = _publish(with_title("In community A"), community=community)
    in_b = _publish(with_title("In community B"), community=community)
    outside = _publish(with_title("Outside"))

    RDMRecord.index.refresh()
    return {
        "in_ids": sorted([in_a.id, in_b.id]),
        "all_ids": sorted([in_a.id, in_b.id, outside.id]),
        "community_uuid": str(community._record.id),
    }


def _ids(result):
    return sorted(r["id"] for r in result.hits)


def test_scoped_ids_match(published):
    """Community-scoped scan: both paths must yield the same record set.

    Scoping by a test-local community UUID makes this exact: no cross-test
    leakage because each run creates a fresh community.
    """
    uuid = published["community_uuid"]

    scroll_res, scroll_total = _scan_records(system_identity, uuid, use_pit=False)
    pit_res, pit_total = _scan_records(system_identity, uuid, use_pit=True)

    expected = published["in_ids"]
    assert _ids(scroll_res) == _ids(pit_res) == expected
    assert scroll_total == pit_total == len(expected)


def test_scoped_projections_match(published):
    """Both paths project each record through the same schema + links tpl —
    the full projected dicts must match, not just the IDs.
    """
    uuid = published["community_uuid"]

    def by_id(result):
        return {r["id"]: r for r in result.hits}

    scroll_res, _ = _scan_records(system_identity, uuid, use_pit=False)
    pit_res, _ = _scan_records(system_identity, uuid, use_pit=True)

    assert by_id(scroll_res) == by_id(pit_res)


def test_unscoped_ids_match(published):
    """Unscoped scan: both paths must agree, and include our records.

    The OpenSearch index is not torn down between function-scoped tests, so
    this asserts set equality between the two paths (the real claim) plus a
    subset check against what this test published.
    """
    scroll_res, scroll_total = _scan_records(system_identity, None, use_pit=False)
    pit_res, pit_total = _scan_records(system_identity, None, use_pit=True)

    scroll_ids = _ids(scroll_res)
    pit_ids = _ids(pit_res)

    assert scroll_ids == pit_ids
    assert set(published["all_ids"]) <= set(scroll_ids)
    # Totals from both paths must match what iteration actually yields.
    # (No concurrent writes in tests, so count() and scroll agree exactly.)
    assert scroll_total == pit_total == len(pit_ids)


def test_pit_pagination(published):
    """Force multi-page PIT traversal with size=1 and confirm no hits are lost."""
    search = service._search(
        "scan",
        system_identity,
        {"allversions": True, "include_deleted": True},
        search_preference=None,
        q="",
    )
    hits = list(pit_scan(index=search._index, body=search.to_dict(), size=1))
    ids = [h.to_dict()["id"] for h in hits]

    # Each document must appear exactly once — no duplicates across pages.
    assert len(ids) == len(set(ids))
    # Our records from this test run are all present.
    assert set(published["all_ids"]) <= set(ids)
