# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Mirador preview."""

from flask import current_app, render_template


def can_preview(file):
    """Check if file can be previewed by this previewer.

    :param file: The file to be previewed.
    :returns: Boolean.
    """
    # supported_extensions list needs . prefixed -
    preview_extensions = current_app.config["MIRADOR_PREVIEW_EXTENSIONS"]
    supported_extensions = ["." + ext for ext in preview_extensions]
    return (
        file.has_extensions(*supported_extensions) and file.record.data["is_published"]
    )


def preview(file):
    """Render template."""
    return render_template(
        "invenio_app_rdm/records/mirador_preview.html",
        file=file,
        ui_config=current_app.config["MIRADOR_PREVIEW_CONFIG"],
    )
