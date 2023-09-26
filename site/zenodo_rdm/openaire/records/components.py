# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE record component."""

from flask import current_app
from invenio_rdm_records.services.components.record_deletion import (
    RecordDeletionComponent,
)
from invenio_records_resources.services.uow import TaskOp

from zenodo_rdm.openaire.tasks import openaire_delete, openaire_direct_index


class OpenAIREComponent(RecordDeletionComponent):
    """Service component for custom fields."""

    def publish(self, identity, draft=None, record=None):
        """Publish handler."""
        is_openaire_enabled = current_app.config.get("OPENAIRE_DIRECT_INDEXING_ENABLED")
        if is_openaire_enabled:
            self.uow.register(TaskOp(openaire_direct_index, record_id=record["id"]))

    def delete_record(self, identity, data=None, record=None, **kwargs):
        """Remove record from OpenAIRE."""
        is_openaire_enabled = current_app.config.get("OPENAIRE_DIRECT_INDEXING_ENABLED")
        if is_openaire_enabled:
            self.uow.register(TaskOp(openaire_delete, record_id=record["id"]))

    def restore_record(self, identity, data=None, record=None, **kwargs):
        """Restored record from OpenAIRE."""
        is_openaire_enabled = current_app.config.get("OPENAIRE_DIRECT_INDEXING_ENABLED")
        if is_openaire_enabled:
            self.uow.register(TaskOp(openaire_direct_index, record_id=record["id"]))
