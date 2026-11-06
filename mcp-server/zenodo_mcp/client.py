# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Small async client for the Zenodo (InvenioRDM) REST API."""

from __future__ import annotations

import mimetypes
import os
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server.mcpserver.exceptions import ToolError

DEFAULT_BASE_URL = "https://zenodo.org"
RDM_JSON = "application/vnd.inveniordm.v1+json"

_DOI_RE = re.compile(r"10\.5281/zenodo\.(\d+)", re.IGNORECASE)
_URL_RE = re.compile(r"/(?:records|record|deposit|uploads)/(\d+)")
_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_RECORD_BODY_RE = re.compile(
    r"^/(?:user/)?records(?:/[^/]+(?:/draft|/versions|/draft/actions/publish)?)?$"
    r"|^/communities/[^/]+/records$"
)


class ZenodoError(ToolError):
    """An API failure, phrased so an agent can act on it.

    It subclasses ``ToolError`` so the MCP server reports the message to the
    model as a normal tool error instead of a crash.
    """


@dataclass(frozen=True)
class Settings:
    """Runtime settings, read from the environment."""

    base_url: str = DEFAULT_BASE_URL
    token: str | None = None
    read_only: bool = False
    timeout: float = 60.0
    upload_dir: Path | None = None

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from ``ZENODO_*`` environment variables."""
        return cls(
            base_url=os.environ.get("ZENODO_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            token=os.environ.get("ZENODO_TOKEN") or None,
            read_only=os.environ.get("ZENODO_READ_ONLY", "").lower()
            in ("1", "true", "yes"),
            timeout=float(os.environ.get("ZENODO_TIMEOUT", "60")),
            upload_dir=(
                Path(os.environ["ZENODO_UPLOAD_DIR"]).expanduser().resolve()
                if os.environ.get("ZENODO_UPLOAD_DIR")
                else None
            ),
        )

    @property
    def can_write(self) -> bool:
        """Whether write tools should be offered."""
        return bool(self.token) and not self.read_only


def parse_record_id(value: str) -> str:
    """Turn a record id, Zenodo DOI or Zenodo URL into a bare record id.

    >>> parse_record_id("1234")
    '1234'
    >>> parse_record_id("10.5281/zenodo.1234")
    '1234'
    >>> parse_record_id("https://doi.org/10.5281/zenodo.1234")
    '1234'
    >>> parse_record_id("https://zenodo.org/records/1234/files/a.csv")
    '1234'
    """
    value = value.strip()
    if value.isdigit():
        return value
    for pattern in (_DOI_RE, _URL_RE):
        match = pattern.search(value)
        if match:
            return match.group(1)
    raise ZenodoError(
        f"Could not read a Zenodo record id from {value!r}. Pass a numeric id "
        "(e.g. '1234'), a Zenodo DOI ('10.5281/zenodo.1234') or a record URL. "
        "For a DOI from another registry, use zenodo_search_records with "
        "query 'doi:\"<doi>\"'."
    )


def safe_slug(value: str) -> str:
    """Validate a community slug or id before putting it in a URL path.

    >>> safe_slug("zenodo")
    'zenodo'
    >>> safe_slug("../admin")
    Traceback (most recent call last):
    ...
    zenodo_mcp.client.ZenodoError: Invalid community '../admin'. Use a slug like 'zenodo' or a community id.
    """
    if not _SLUG_RE.match(value or ""):
        raise ZenodoError(
            f"Invalid community {value!r}. Use a slug like 'zenodo' or a community id."
        )
    return value


def file_key(value: str) -> str:
    """URL-encode a file name, rejecting names that would change the path.

    >>> file_key("light curve.csv")
    'light%20curve.csv'
    >>> file_key("a/b.txt")
    'a%2Fb.txt'
    """
    if value in ("", ".", ".."):
        raise ZenodoError(f"Invalid file name {value!r}.")
    return quote(value, safe="")


class ZenodoClient:
    """Thin wrapper over ``httpx.AsyncClient`` with Zenodo error handling."""

    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        """Create a client; ``transport`` lets tests stub the network."""
        self.settings = settings
        headers = {"Accept": "application/json", "User-Agent": "zenodo-mcp"}
        if settings.token:
            headers["Authorization"] = f"Bearer {settings.token}"
        self._http = httpx.AsyncClient(
            base_url=f"{settings.base_url}/api",
            headers=headers,
            timeout=settings.timeout,
            transport=transport,
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        content: Any = None,
        headers: dict[str, str] | None = None,
        auth_required: bool = False,
    ) -> Any:
        """Send a request and return decoded JSON (or ``None`` when empty).

        Record and draft bodies are requested in the native InvenioRDM
        format; other endpoints (files, vocabularies, requests) only speak
        plain JSON.
        """
        if _RECORD_BODY_RE.search(path):
            headers = {"Accept": RDM_JSON, **(headers or {})}
        if auth_required and not self.settings.token:
            raise ZenodoError(
                "This action needs a Zenodo personal access token. Create one at "
                f"{self.settings.base_url}/account/settings/applications/ with the "
                "'deposit:write' and 'deposit:actions' scopes, then set ZENODO_TOKEN."
            )
        if params:
            params = {k: v for k, v in params.items() if v not in (None, "")}
        try:
            response = await self._http.request(
                method, path, params=params, json=json, content=content, headers=headers
            )
        except httpx.TimeoutException as exc:
            raise ZenodoError(
                f"Zenodo did not answer within {self.settings.timeout:.0f}s "
                f"({method} {path}). Try again, or raise ZENODO_TIMEOUT."
            ) from exc
        except httpx.HTTPError as exc:
            raise ZenodoError(
                f"Could not reach {self.settings.base_url}: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise ZenodoError(_describe_error(response, method, path))
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    async def get(self, path: str, **kwargs: Any) -> Any:
        """Shortcut for ``GET``."""
        return await self.request("GET", path, **kwargs)

    async def upload_file(self, record_id: str, path: Path, key: str) -> dict:
        """Upload a local file to a draft with the three-step files API."""
        base = f"/records/{record_id}/draft/files"
        quoted = file_key(key)
        await self.request("POST", base, json=[{"key": key}], auth_required=True)
        mimetype = mimetypes.guess_type(key)[0] or "application/octet-stream"
        await self.request(
            "PUT",
            f"{base}/{quoted}/content",
            content=_read_chunks(path),
            headers={
                "Content-Type": "application/octet-stream",
                "Content-Length": str(path.stat().st_size),
            },
            auth_required=True,
        )
        result = await self.request(
            "POST", f"{base}/{quoted}/commit", auth_required=True
        )
        if isinstance(result, dict):
            result.setdefault("mimetype", mimetype)
        return result


async def _read_chunks(path: Path, size: int = 1024 * 1024) -> AsyncIterator[bytes]:
    """Stream a file in chunks so large uploads stay out of memory."""
    with path.open("rb") as handle:
        while chunk := handle.read(size):
            yield chunk


def _describe_error(response: httpx.Response, method: str, path: str) -> str:
    status = response.status_code
    try:
        body = response.json()
    except ValueError:
        body = {}
    message = body.get("message") if isinstance(body, dict) else None
    details = []
    if isinstance(body, dict):
        for err in body.get("errors") or []:
            field = err.get("field", "?")
            msgs = err.get("messages") or [err.get("message", "")]
            details.append(f"{field}: {'; '.join(str(m) for m in msgs)}")

    hint = {
        401: "The token is missing or invalid. Check ZENODO_TOKEN.",
        403: "The token was refused. zenodo.org and sandbox.zenodo.org have "
        "separate accounts and tokens, so check that ZENODO_TOKEN was created on "
        "ZENODO_BASE_URL. Otherwise the token lacks a scope (writes need "
        "'deposit:write', publishing needs 'deposit:actions'), or the record "
        "belongs to someone else.",
        404: "Nothing exists at this id. Check the id, and note that drafts are "
        "only visible to their owner (use zenodo_list_my_records).",
        429: "Zenodo's rate limit was hit. Wait a minute before retrying.",
    }.get(status)

    text = f"Zenodo returned HTTP {status} for {method} {path}"
    if message:
        text += f": {message}"
    if details:
        text += "\nField errors:\n- " + "\n- ".join(details)
    if hint:
        text += f"\n{hint}"
    return text
