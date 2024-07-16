# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy REST API client."""

import os
from typing import BinaryIO

import requests


class ZenodoClientError(Exception):
    """Zenodo REST API client error."""

    def __init__(self, message, response):
        """Initialize error."""
        super().__init__(message)
        self.response = response


class ZenodoClient:
    """Zenodo REST API client."""

    DOMAINS = {
        "local": "localhost:5000",
        "zenodo-prod": "zenodo.org",
        "zenodo-qa": "sandbox.zenodo.org",
        "zenodo-rdm-prod": "zenodo-rdm.web.cern.ch",
        "zenodo-rdm-qa": "zenodo-rdm-qa.web.cern.ch",
    }

    def __init__(self, token=None, *, base_url=None):
        """Initialize client."""
        self._token = token
        self.base_url = self.DOMAINS.get(base_url, base_url)
        self.session = self._create_session(token)

    @property
    def deposit_url(self):
        """Legacy deposit REST API endpoint URL."""
        return f"https://{self.base_url}/api/deposit/depositions"

    @staticmethod
    def _create_session(token):
        """Create requests session."""
        session = requests.Session()
        session.verify = False
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session

    def _raise_resp(self, message, response):
        """Raise exception on bad response codes."""
        if not response.ok:
            raise ZenodoClientError(message, response)

    def _upload_file(self, deposit, file: BinaryIO, use_files_api=True):
        """Upload a file to the legacy REST API."""
        if use_files_api:
            bucket_url = deposit["links"]["bucket"]
            upload_resp = self.session.put(f"{bucket_url}/{file.name}", data=file)
        else:
            files_url = deposit["links"]["files"]
            upload_resp = self.session.post(
                files_url,
                data={"name": file.name},
                files={"file": file},
            )

        self._raise_resp("Failed to upload file", upload_resp)
        return upload_resp

    def _publish(self, resp):
        """Publish a deposit."""
        publish_url = resp.json()["links"]["publish"]
        publish_resp = self.session.post(publish_url)
        self._raise_resp("Failed to publish deposit", publish_resp)
        return publish_resp

    def create(
        self,
        data: dict,
        files: list[BinaryIO],
        publish: bool = True,
        file_upload_kwargs: dict = None,
    ):
        """Create a new record with files."""
        created_resp = self.session.post(self.deposit_url, json=data)
        self._raise_resp("Failed to create deposit", created_resp)

        for f in files:
            self._upload_file(created_resp.json(), file=f, **(file_upload_kwargs or {}))
        if not publish:
            return created_resp

        return self._publish(created_resp)

    def update(
        self,
        id: str,
        data: dict,
        files: list[BinaryIO] = None,
        publish: bool = True,
    ):
        """Update an existing record."""
        deposit_url = f"{self.base_url}/{id}"
        get_resp = self.session.get(deposit_url)
        self._raise_resp("Failed to fetch deposit", get_resp)

        edit_url = get_resp.json()["links"]["edit"]
        edit_resp = self.session.post(edit_url)
        self._raise_resp("Failed to edit deposit", edit_resp)

        update_resp = self.session.put(deposit_url, json=data)
        self._raise_resp("Failed to update deposit", update_resp)

        if not publish:
            return update_resp

        return self._publish(update_resp)


client = ZenodoClient(
    token=os.environ.get("ZENODO_TOKEN"),
    base_url=os.environ.get("ZENODO_BASE_URL"),
)
