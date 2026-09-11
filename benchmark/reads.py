import random
from urllib.parse import urlparse

from locust import HttpUser, task

from common import cached_csrf_login, load_accounts, record_id_pool

RECORD_IDS = []
ACCOUNTS = None
SEARCH_TERMS = ["data", "climate", "genome", "machine learning", "survey", "covid"]
COMMUNITIES_LOGOS = False


def _ensure_record_ids():
    global RECORD_IDS
    if not RECORD_IDS:
        RECORD_IDS = record_id_pool()
    return RECORD_IDS


def _ensure_accounts():
    global ACCOUNTS
    if ACCOUNTS is None:
        ACCOUNTS = load_accounts()
    return ACCOUNTS


class _PublicBrowsingTask(HttpUser):
    """Shared by anonymous and authenticated readers."""

    def on_start(self):
        self.client.verify = False
        self.label = "anon"

    @task(5)
    def home_page(self):
        self.client.get("/", name=f"[{self.label}] / [home]")

    @task(5)
    def record_landing_page(self):
        record_id = random.choice(_ensure_record_ids())
        self.client.get(
            f"/records/{record_id}", name=f"[{self.label}] /records/[random id]"
        )

    # Tasks reprenseting the calls that are made in production
    @task(10)
    def favicon(self):
        self.client.get(
            "/static/favicon.ico", name=f"[{self.label}] /static/favicon.ico"
        )

    @task(10)
    def records_api(self):
        self.client.get("/api/records", name=f"[{self.label}] /api/records")

    @task(10)
    def search(self):
        action = random.choice([1, 2, 3])
        if action == 1:
            self.client.get(
                f"/search?q={random.choice(_ensure_record_ids())}",
                name=f"[{self.label}] /search [by record id]",
            )
        if action == 2:
            self.client.get(
                f"/search?q={random.choice(SEARCH_TERMS)}",
                name=f"[{self.label}] /search [by search term]",
            )
        if action == 3:
            self.client.get("/search", name=f"[{self.label}] /search [no args given]")

    @task(10)
    def doi_badge(self):
        self.client.get(
            f"/badge/DOI/10.51/zenodo.{random.choice(_ensure_record_ids())}.svg",
            name=f"[{self.label}] /badge/DOI/10.51/zenodo.[random record id].svg",
        )

    @task(10)
    def get_logos(self):
        if not hasattr(self, "logos"):
            response = self.client.get("/api/communities")
            self.logos = [
                hit["links"]["logo"] for hit in response.json()["hits"]["hits"]
            ]
        self.client.get(
            urlparse(random.choice(self.logos)).path,
            name=f"[{self.label}] /api/communities/[random id]/logo",
        )


class AnonymousReadUser(_PublicBrowsingTask):
    weight = 1


class AuthenticaedReadUser(_PublicBrowsingTask):
    weight = 1

    def on_start(self):
        self.client.verify = False
        self.label = "auth"
        account = _ensure_accounts().next()
        cached_csrf_login(self.client, account)

    @task(5)
    def my_uploads(self):
        r = self.client.get("/me/uploads", name=f"[{self.label}] /me/uploads")
