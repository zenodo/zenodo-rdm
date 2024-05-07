# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Mirador preview."""

from os.path import splitext

from flask import current_app, render_template
from werkzeug.local import LocalProxy


def can_preview(file):
    """Check if file can be previewed by this previewer.

    :param file: The file to be previewed.
    :returns: Boolean.
    """
    # supported_extensions list needs . prefixed -
    preview_extensions = current_app.config["MIRADOR_PREVIEW_EXTENSIONS"]
    supported_extensions = ["." + ext for ext in preview_extensions]

    return file.has_extensions(*supported_extensions)


def preview(file):
    """Render template."""
    media_file_name = file.filename + ".ptif"

    ext = splitext(file.filename)[1].lower()[1:]
    format = (
        ext
        if ext in current_app.config["IIIF_SIMPLE_PREVIEWER_NATIVE_EXTENSIONS"]
        else "jpg"
    )
    size = current_app.config["IIIF_SIMPLE_PREVIEWER_SIZE"]
    iiif_simple_url = (
        f"{file.data['links']['iiif_base']}/full/{size}/0/default.{format}"
    )
    media_file = (
        file.record._record.media_files.get(media_file_name)
        if file.record._record.media_files.enabled
        else None
    )

    return render_template(
        "invenio_app_rdm/records/mirador_preview.html",
        css_bundles=["mirador-previewer.css"],
        file=file,
        file_url=iiif_simple_url,
        media_file=media_file,
        ui_config=current_app.config["MIRADOR_PREVIEW_CONFIG"],
    )
