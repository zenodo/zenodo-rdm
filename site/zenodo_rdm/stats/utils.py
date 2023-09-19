# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Statistics utilities."""

import itertools
from invenio_rdm_records.proxies import current_rdm_records_service

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


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
