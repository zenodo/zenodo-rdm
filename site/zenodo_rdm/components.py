# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Custom Metadata component."""

from invenio_drafts_resources.services.records.components import ServiceComponent


class CustomMetadataComponent(ServiceComponent):
    """Service component for custom metadata.

    This component comes in handy for migrations/custom updates for the Zenodo instance.
    """

    def _update_thesis_to_dissertation(self, record):
        """Update 'publication-thesis' to 'publication-dissertation'."""
        if record.metadata.get("resource_type", {}).get("id") == "publication-thesis":
            record.metadata["resource_type"]["id"] = "publication-dissertation"

    def create(self, identity, data=None, record=None, **kwargs):
        """Update record metadata."""
        self._update_thesis_to_dissertation(record)

    def update_draft(self, identity, data=None, record=None, **kwargs):
        """Update record metadata."""
        self._update_thesis_to_dissertation(record)

    def publish(self, identity, draft=None, record=None, **kwargs):
        """Update record metadata."""
        self._update_thesis_to_dissertation(record)

    def edit(self, identity, draft=None, record=None, **kwargs):
        """Update record metadata."""
        self._update_thesis_to_dissertation(record)
