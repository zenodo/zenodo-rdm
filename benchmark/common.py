import csv
import itertools
import json
import os
import threading
import uuid
from pathlib import Path
from random import randint

import requests

cur_dir = Path(__file__).parent
ACCOUNTS_CSV = cur_dir / "accounts.csv"
SESSION_CACHE_FILE = cur_dir / "session_cache.json"
_session_cache_lock = threading.Lock()

# To be able to read logs better
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AccountPool:
    """Round-robin picker from provisioned test accounts."""

    def __init__(self, accounts):
        if not accounts:
            raise RuntimeError(
                f"No accounts found in {ACCOUNTS_CSV}.\n\n"
                "Run provision_accounts.sh first to create a pool of "
                "test accounts."
            )
        self._accounts = accounts
        self._cycle = itertools.cycle(accounts)
        self._lock = threading.Lock()

    def next(self):
        with self._lock:
            return next(self._cycle)


def load_accounts() -> AccountPool:
    if not ACCOUNTS_CSV.exists():
        raise FileNotFoundError()
    with ACCOUNTS_CSV.open(newline="") as f:
        accounts = [(row["email"], row["password"]) for row in csv.DictReader(f)]
    return AccountPool(accounts)


def crsf_headers(client):
    csrf_token = client.cookies.get("csrftoken")
    if not csrf_token:
        raise RuntimeError("no csrf cookie set")
    return {"X-CSRFToken": csrf_token}


def csrf_login(client, account) -> dict[str, str]:
    email, password = account
    response = client.post(
        "/api/login",
        data={"email": email, "password": password},
        name="/login",
    )
    response.raise_for_status()
    csrf_token = client.cookies.get("csrftoken")
    if not csrf_token:
        raise RuntimeError("did not set a csrftoken cookie")
    return {"X-CSRFToken": csrf_token}


def _load_session_cache():
    with _session_cache_lock:
        if not SESSION_CACHE_FILE.exists():
            return {}
        try:
            return json.loads(SESSION_CACHE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}


def _save_session_cache(cache) -> None:
    with _session_cache_lock:
        SESSION_CACHE_FILE.write_text(json.dumps(cache))


def cached_csrf_login(client, account) -> dict[str, str]:
    email, _ = account
    cache = _load_session_cache()
    cached = cache.get(email)

    if cached:
        requests.utils.cookiejar_from_dict(cached["cookies"], cookiejar=client.cookies)
        check = client.get(
            "/account/settings/profile",
            name="/account/settings/profile [session check]",
        )
        if check.status_code == 200:
            return {"X-CSRFToken": cached["csrf_token"]}
        client.cookies.clear()
    headers = csrf_login(client, account)
    cache[email] = {
        "cookies": requests.utils.dict_from_cookiejar(client.cookies),
        "csrf_token": headers["X-CSRFToken"],
    }
    _save_session_cache(cache)
    return headers


def record_id_pool() -> list[int]:
    """Return a list of random ids between 0 and 200,
    this is the number of records created on seting up the
    project locally, so it will always have this number of records.

    TODO: Later we can select length and pre-defined ids.
    """
    return [randint(1, 200) for _ in range(0, 50)]


def minimal_metadata(title_suffix: str) -> dict:
    """
    based on minimal_record in site/tests/conftest.py
    """
    tag = f"[locust-loadtest] {uuid.uuid4()} ({title_suffix})"
    return {
        "pids": {},
        "access": {
            "record": "public",
            "files": "restricted",
        },
        "files": {
            "enabled": True,
        },
        "metadata": {
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Loadtest",
                        "given_name": "Locust",
                        "type": "personal",
                    }
                },
            ],
            "publication_date": "2020-06-01",
            "publisher": "Acme Inc",
            "resource_type": {"id": "image-photo"},
            "title": tag,
        },
    }


_SIZE_TIERS = {
    "small": (200 * 1024, "paper.pdf"),
    "medium": (5 * 1024 * 1024, "dataset.csv"),  # 5.2mb
    # "large": (20 * 100 * 1024 * 1024, "big-dataset.zip") # 2gb
    "large": (100 * 1024 * 1024, "big-dataset.zip"),
}


def random_file(size_tier: str) -> tuple[str, bytes]:
    size, filename = _SIZE_TIERS[size_tier]
    return f"{uuid.uuid4()}_{filename}", os.urandom(size)
