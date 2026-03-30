# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Statistics utilities."""

import itertools
from functools import lru_cache

from invenio_rdm_records.proxies import current_rdm_records_service


def chunkify(iterable, n):
    """Create equally sized tuple-chunks from an iterable."""
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


@lru_cache(maxsize=1024)
def fetch_record(recid):
    """Cached record fetch."""
    record = current_rdm_records_service.record_cls.pid.resolve(recid)
    return {
        "oai_id": record.get("oai", {}).get("identifier"),
        "title": record.get("metadata", {}).get("title")[:150],  # max 150 characters
    }
