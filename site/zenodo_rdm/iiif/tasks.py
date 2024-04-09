# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""IIIF celery tasks."""


from celery import shared_task
from flask import current_app

try:
    import pyvips

    HAS_VIPS = True

except ModuleNotFoundError:
    # Python module pyvips not installed
    HAS_VIPS = False

except OSError:
    # Underlying library libvips not installed
    HAS_VIPS = False


@shared_task
def pyvips_process():
    """Process an image with pyvips."""
    if HAS_VIPS:
        source_image = pyvips.Image.new_from_file("./app_data/img/covid-19.png")
        source_image.tiffsave(
            "dst.tif",
            tile=True,
            pyramid=True,
            compression="jpeg",
            Q=90,
            tile_width=256,
            tile_height=256,
        )
    else:
        current_app.logger.warning(
            "Skipping pyvips_process since either pyvips or libvips are not installed"
        )
