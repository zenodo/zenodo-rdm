# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Services for IIIf."""

from flask import current_app
from invenio_drafts_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.uow import TaskOp

from zenodo_rdm.iiif.tasks import generate_zoomable_image


class IIIFTilesComponent(ServiceComponent):
    """IIIF tiles generation component."""

    def publish(self, identity, draft=None, record=None):
        """Publish handler."""
        if not current_app.config["TILES_GENERATION_ENABLED"]:
            return

        # If it's not the first publication, skip
        if draft.is_published:
            return

        iiif_formats = current_app.config["IIIF_FORMATS"]
        for key, record_file in record.files.entries.items():
            if record_file.file.ext in iiif_formats:
                self.uow.register(
                    TaskOp(
                        generate_zoomable_image,
                        record_id=record.pid.pid_value,
                        file_key=key,
                    )
                )
