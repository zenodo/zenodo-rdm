# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo migrator requests transformers."""

from invenio_rdm_migrator.streams.requests import RequestTransform

from .entries.requests import ZenodoRequestEntry


class ZenodoRequestTransform(RequestTransform):
    """Transform a Zenodo request into RDM."""

    def _request(self, entry):
        """Transform the request."""
        return ZenodoRequestEntry().transform(entry)
