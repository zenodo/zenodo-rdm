# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Turn Zenodo API payloads into compact summaries for language models."""

from __future__ import annotations

import re
from typing import Any

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def strip_html(text: str | None, limit: int | None = None) -> str | None:
    """Remove HTML tags and squeeze whitespace, optionally truncating.

    >>> strip_html("<p>Hello <b>world</b></p>")
    'Hello world'
    >>> strip_html("abcdef", limit=3)
    'abc…'
    """
    if not text:
        return None
    clean = _SPACE_RE.sub(" ", _TAG_RE.sub(" ", text)).strip()
    if limit and len(clean) > limit:
        return clean[:limit].rstrip() + "…"
    return clean


def _title(value: Any) -> str | None:
    """Pick the English title from a vocabulary entry."""
    if isinstance(value, dict):
        title = value.get("title")
        if isinstance(title, dict):
            return title.get("en") or next(iter(title.values()), None)
        return title or value.get("id")
    return value


def _creator(entry: dict) -> dict:
    person = entry.get("person_or_org", {})
    out: dict[str, Any] = {"name": person.get("name")}
    orcid = next(
        (
            i["identifier"]
            for i in person.get("identifiers", [])
            if i.get("scheme") == "orcid"
        ),
        None,
    )
    if orcid:
        out["orcid"] = orcid
    affiliations = [
        a.get("name") for a in entry.get("affiliations", []) if a.get("name")
    ]
    if affiliations:
        out["affiliations"] = affiliations
    if entry.get("role"):
        out["role"] = _title(entry["role"])
    return out


def summarize_record(record: dict, description_limit: int | None = 500) -> dict:
    """Summarize a record or draft in the InvenioRDM JSON format."""
    metadata = record.get("metadata", {})
    pids = record.get("pids", {})
    parent = record.get("parent", {})
    links = record.get("links", {})
    files = record.get("files", {})
    stats = (record.get("stats") or {}).get("this_version") or {}
    access = record.get("access", {})

    summary: dict[str, Any] = {
        "id": record.get("id"),
        "title": metadata.get("title"),
        "doi": (pids.get("doi") or {}).get("identifier"),
        "concept_doi": ((parent.get("pids") or {}).get("doi") or {}).get("identifier"),
        "status": record.get("status"),
        "is_published": record.get("is_published"),
        "is_draft": record.get("is_draft"),
        "publication_date": metadata.get("publication_date"),
        "version": metadata.get("version"),
        "resource_type": (metadata.get("resource_type") or {}).get("id"),
        "creators": [_creator(c) for c in metadata.get("creators", [])],
        "description": strip_html(metadata.get("description"), description_limit),
        "keywords": [
            s.get("subject") for s in metadata.get("subjects", []) if s.get("subject")
        ],
        "license": [r.get("id") or _title(r) for r in metadata.get("rights", [])],
        "access": {
            "record": access.get("record"),
            "files": access.get("files"),
        },
        "communities": [
            c.get("slug") or c.get("id")
            for c in (parent.get("communities") or {}).get("entries", [])
        ],
        "file_count": files.get("count"),
        "total_bytes": files.get("total_bytes"),
        "latest_version": (record.get("versions") or {}).get("is_latest"),
        "views": stats.get("unique_views"),
        "downloads": stats.get("unique_downloads"),
        "url": links.get("self_html"),
    }
    return {k: v for k, v in summary.items() if v not in (None, [], {})}


def summarize_file(entry: dict) -> dict:
    """Summarize a file entry from ``/records/{id}/files``."""
    links = entry.get("links", {})
    return {
        k: v
        for k, v in {
            "key": entry.get("key"),
            "size": entry.get("size"),
            "checksum": entry.get("checksum"),
            "mimetype": entry.get("mimetype"),
            "status": entry.get("status"),
            "download_url": links.get("content"),
        }.items()
        if v is not None
    }


def summarize_community(community: dict) -> dict:
    """Summarize a community."""
    metadata = community.get("metadata", {})
    links = community.get("links", {})
    return {
        k: v
        for k, v in {
            "id": community.get("id"),
            "slug": community.get("slug"),
            "title": metadata.get("title"),
            "type": _title(metadata.get("type")),
            "description": strip_html(metadata.get("description"), 300),
            "website": metadata.get("website"),
            "organizations": [o.get("name") for o in metadata.get("organizations", [])],
            "visibility": (community.get("access") or {}).get("visibility"),
            "url": links.get("self_html"),
        }.items()
        if v not in (None, [], "")
    }


def summarize_vocabulary(entry: dict) -> dict:
    """Summarize a vocabulary, affiliation, funder or award entry."""
    out: dict[str, Any] = {"id": entry.get("id"), "title": _title(entry)}
    if entry.get("name"):
        out["title"] = entry["name"]
    if entry.get("acronym"):
        out["acronym"] = entry["acronym"]
    if entry.get("number"):
        out["number"] = entry["number"]
    if isinstance(entry.get("funder"), dict):
        out["funder"] = entry["funder"].get("name") or entry["funder"].get("id")
    if entry.get("country_name") or entry.get("country"):
        out["country"] = entry.get("country_name") or entry.get("country")
    url = (entry.get("props") or {}).get("url")
    if url:
        out["url"] = url
    return {k: v for k, v in out.items() if v}


def page_info(payload: dict, page: int, size: int) -> dict:
    """Pagination block shared by all list tools."""
    total = (payload.get("hits") or {}).get("total", 0)
    if isinstance(total, dict):  # some endpoints return {"value": n}
        total = total.get("value", 0)
    return {
        "total": total,
        "page": page,
        "size": size,
        "has_more": page * size < total,
    }
