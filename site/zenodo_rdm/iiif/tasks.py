# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tasks for statistics."""

from celery import shared_task

from invenio_rdm_records.proxies import current_rdm_records_service
from .utils import LocalTilesStorage

tif_store = LocalTilesStorage(base_path="/images")

@shared_task(ignore_result=True, )
def generate_zoomable_image(record_id, file_key, params=None):
    """Generate pyramidal tiff."""
    record = current_rdm_records_service.record_cls.pid.resolve(record_id)
    tif_store.save(record, file_key)
