# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE record component."""

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.files.processors import ProcessorRunner
from invenio_records_resources.services.uow import TaskOp

from zenodo_rdm.iiif.tasks import generate_zoomable_image


class IIIFComponent(ServiceComponent):
    """Service component for IIIF."""

    def publish(self, identity, draft=None, record=None):
        """Publish handler."""

        # TODO Makes sense to add the below if we move it to records-resources/rdm-records
        iiif_generate_tiles = current_app.config.get("IIIF_GENERATE_TILES")
        if not iiif_generate_tiles:
            return

        for fname, file in record.files.items():
            ProcessorRunner(self.service.config.file_processors).run(file, uow=self.uow)
