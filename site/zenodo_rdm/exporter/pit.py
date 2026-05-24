# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Point-in-Time based scan helper for the exporter.

Mirrors the iteration shape of ``opensearch_dsl.Search.scan()`` but uses
OpenSearch's Point-in-Time API with ``search_after`` pagination instead of the
scroll API. PIT decouples the snapshot from pagination, so long per-record
processing between batches does not expire a shard-bound scroll context.
"""

from invenio_search import current_search_client


class _Meta(dict):
    """Dict that also supports attribute-style access (like dsl ``HitMeta``)."""

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(key) from e


class _Hit:
    """Minimal DSL-Hit-like wrapper exposing ``to_dict()`` and ``meta``.

    ``RecordList.hits`` calls ``hit.to_dict()`` and (in ``RDMRecordList``)
    reads ``hit.meta["index"]`` to tell records apart from drafts, so both
    need to be available.
    """

    __slots__ = ("_src", "meta")

    def __init__(self, raw):
        self._src = raw["_source"]
        self.meta = _Meta(
            {
                "index": raw.get("_index"),
                "id": raw.get("_id"),
                "score": raw.get("_score"),
            }
        )

    def to_dict(self):
        return self._src


class _PitScan:
    """Iterable PIT scan with a snapshot-accurate ``.total``.

    Creating the PIT and counting against it happen together in ``__init__``,
    so ``.total`` and the iteration come from the same frozen snapshot — no
    drift even if records are published or deleted during the scan.
    """

    def __init__(self, index, body, *, size=1000, keep_alive="5m"):
        self._client = current_search_client
        self._size = size
        self._keep_alive = keep_alive
        # _id is the portable tiebreaker across OpenSearch 2.x — _shard_doc
        # only landed in recent builds.
        self._sort = list(body.get("sort") or []) + [{"_id": "asc"}]
        # PIT queries are not bound to an index and cannot carry from/sort.
        self._body = {k: v for k, v in body.items() if k not in ("from", "sort")}
        self._pit_id = self._client.create_pit(
            index=index, keep_alive=keep_alive
        )["pit_id"]
        # Count against the same PIT — total matches exactly what __iter__ yields.
        count_resp = self._client.search(
            body={
                "query": self._body.get("query", {"match_all": {}}),
                "pit": {"id": self._pit_id, "keep_alive": keep_alive},
                "size": 0,
                "track_total_hits": True,
            }
        )
        self.total = count_resp["hits"]["total"]["value"]

    def __iter__(self):
        pit_id = self._pit_id
        search_after = None
        try:
            while True:
                query = {
                    **self._body,
                    "size": self._size,
                    "sort": self._sort,
                    "pit": {"id": pit_id, "keep_alive": self._keep_alive},
                }
                if search_after is not None:
                    query["search_after"] = search_after

                resp = self._client.search(body=query)
                hits = resp["hits"]["hits"]
                if not hits:
                    return

                for h in hits:
                    yield _Hit(h)

                search_after = hits[-1]["sort"]
                # PIT id may rotate between requests; always pick up the latest.
                pit_id = resp.get("pit_id", pit_id)
        finally:
            # Best-effort cleanup; PIT also expires on its own via keep_alive.
            # Generator may be torn down outside app context — swallow all errors.
            try:
                self._client.delete_pit(body={"pit_id": pit_id})
            except Exception:
                pass


def pit_scan(index, body, *, size=1000, keep_alive="5m"):
    """Create a PIT and return an iterable with a snapshot-accurate ``.total``."""
    return _PitScan(index, body, size=size, keep_alive=keep_alive)
