# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Orcha client."""

import os

import requests


class OrchaClient:
    """Client for the Orcha AI workflow service."""

    def __init__(
        self, key_path=None, key_id=None, tenant=None, base_url=None, ssl_verify=True
    ):
        """Initialize client."""
        self.key_path = key_path
        self.key_id = key_id
        self.tenant = tenant
        self.base_url = base_url
        self.ssl_verify = ssl_verify
        self._private_key = None

    @property
    def private_key(self):
        """Return the private key, loading it lazily from env or file."""
        if self._private_key is None:
            key_content = os.environ.get("ZENODO_ORCHA_PRIVATE_KEY")
            if key_content:
                self._private_key = key_content
            elif self.key_path:
                with open(self.key_path) as f:
                    self._private_key = f.read()
            else:
                raise RuntimeError("No private key configured for Orcha client.")
        return self._private_key

    def trigger_workflow(self, payload, token):
        """Trigger an Orcha workflow with the given payload and token."""
        response = requests.post(
            f"{self.base_url}/workflows",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
            verify=self.ssl_verify,
        )
        response.raise_for_status()
        return response.json()

    def stream_url(self, workflow_id: str, token: str):
        """Create the stream URL for an Orcha workflow."""
        return f"{self.base_url}/workflows/{workflow_id}/stream?token={token}"
