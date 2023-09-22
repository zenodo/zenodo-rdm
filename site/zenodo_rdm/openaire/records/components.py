# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE record component."""

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp

from zenodo_rdm.openaire.tasks import openaire_direct_index


class OpenAIREComponent(ServiceComponent):
    """Service component for custom fields."""

    def publish(self, identity, draft=None, record=None):
        """Publish handler."""
        is_openaire_enabled = current_app.config.get("OPENAIRE_DIRECT_INDEXING_ENABLED")
        if is_openaire_enabled:
            self.uow.register(TaskOp(openaire_direct_index, record_id=record["id"]))
