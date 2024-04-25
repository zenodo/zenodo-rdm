# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tasks for IIIF."""

from celery import shared_task
from flask import current_app
from invenio_rdm_records.proxies import current_rdm_records_service

from zenodo_rdm.iiif.utils import LocalTilesStorage


@shared_task(ignore_result=True)
def generate_zoomable_image(record_id, file_key):
    """Generate pyramidal tiff."""
    tiles_storage_path = current_app.config.get("TILES_STORAGE_PATH")
    tif_store = LocalTilesStorage(base_path=tiles_storage_path)
    record = current_rdm_records_service.record_cls.pid.resolve(record_id)
    tif_store.save(record, file_key)
