import os

from locust import HttpUser, task

from common import (
    cached_csrf_login,
    crsf_headers,
    load_accounts,
    minimal_metadata,
    random_file,
)

ACCOUNTS = None


def _ensure_accounts():
    global ACCOUNTS
    if ACCOUNTS is None:
        ACCOUNTS = load_accounts()
    return ACCOUNTS


def _create_draft(client, metadata):
    response = client.post(
        "/api/records",
        json=metadata,
        headers=crsf_headers(client),
        name="/api/records [crate draft]",
    )
    response.raise_for_status()
    return response.json()


def _upload_file(client, draft, size_tier):
    record_id = draft["id"]
    filename, content = random_file(size_tier)

    response = client.post(
        f"/api/records/{record_id}/draft/files",
        json=[{"key": filename}],
        headers=crsf_headers(client),
        name=f"/api/records/<id>/draft/files [init upload] ({size_tier} file)",
    )
    response.raise_for_status()

    response = client.put(
        f"/api/records/{record_id}/draft/files/{filename}/content",
        data=content,
        headers={**crsf_headers(client), "Content-Type": "application/octet-stream"},
        name=f"/api/records/<id>/draft/files/<key>/content [upload] ({size_tier} file)",
    )
    response.raise_for_status()

    response = client.post(
        f"/api/records/{record_id}/draft/files/{filename}/commit",
        headers=crsf_headers(client),
        name=f"/api/records/<id>/draft/files/<key>/commit ({size_tier} file)",
    )
    response.raise_for_status()


def _publish(client, draft):
    record_id = draft["id"]
    response = client.post(
        f"/api/records/{record_id}/draft/actions/publish",
        headers=crsf_headers(client),
        name="/api/records/<id>/draft/actions/publish",
    )
    response.raise_for_status()


class WriteUser(HttpUser):

    def on_start(self):
        self.client.verify = False
        self.client.headers["Referer"] = self.client.base_url  # Don't remove
        account = _ensure_accounts().next()
        cached_csrf_login(self.client, account)

    def _start_upload(self):
        # load /uploads/new as a real uswer
        self.client.get("/uploads/new")

    @task(10)
    def publish_small_managed_doi(self):
        self._start_upload()
        draft = _create_draft(self.client, minimal_metadata("small/managed-doi"))
        for _ in range(2):
            _upload_file(self.client, draft, "small")
        _publish(self.client, draft)

    @task(10)
    def publish_medium_managed_doi(self):
        self._start_upload()
        draft = _create_draft(self.client, minimal_metadata("medium/managed-doi"))
        for _ in range(2):
            _upload_file(self.client, draft, "medium")
        _publish(self.client, draft)

    @task(1)  # Be careful with this one you can crash your own computer
    def publish_large_managed_doi(self):
        self._start_upload()
        draft = _create_draft(self.client, minimal_metadata("large/managed-doi"))
        for _ in range(2):
            _upload_file(self.client, draft, "large")
        _publish(self.client, draft)

    @task(10)
    def get_names(self):
        self.client.get("/api/names")

    @task(10)
    def get_subjects(self):
        self.client.get("/api/subjects")
