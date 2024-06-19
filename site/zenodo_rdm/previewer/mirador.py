# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Mirador preview."""

from os.path import splitext

from flask import current_app, render_template


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
    record = file.record._record
    tpl_ctx = {}

    # Check the status of the tile generation for the image
    tile_status = None
    if record.media_files.enabled and not record.is_draft:
        tile_file = record.media_files.get(f"{file.filename}.ptif")
        if tile_file is not None and tile_file.processor:
            tile_status = tile_file.processor.get("status")

    show_mirador = tile_status == "finished"
    tpl_ctx["show_mirador"] = show_mirador

    if show_mirador:
        # Add IIIF URLs for Mirador
        tpl_ctx["iiif_canvas_url"] = file.data["links"]["iiif_canvas"]
        tpl_ctx["iiif_manifest_url"] = file.record["links"]["self_iiif_manifest"]
        tpl_ctx["mirador_cfg"] = current_app.config["MIRADOR_PREVIEW_CONFIG"]

        # Generate annotation file content link
        annotation_url = None
        annotation_filename = f"{file.filename}.short.wadm"

        if annotation_filename in record.files:
            annotation_url = (
                f"{file.record['links']['files']}/{annotation_filename}/content"
            )
        elif annotation_filename in record.media_files:
            annotation_url = (
                f"{file.record['links']['media_files']}/{annotation_filename}/content"
            )

        # Update visiblity of annotations panel based on annotation file existence
        if annotation_url:
            tpl_ctx["mirador_cfg"]["window"]["panels"]["annotations"] = True
            tpl_ctx["mirador_cfg"]["window"]["sideBarPanel"] = "annotations"

        tpl_ctx["annotation_url"] = annotation_url

    else:
        # Fallback to simple IIIF image preview
        ext = splitext(file.filename)[1].lower()[1:]
        format = (
            ext
            if ext in current_app.config["IIIF_SIMPLE_PREVIEWER_NATIVE_EXTENSIONS"]
            else "jpg"
        )
        size = current_app.config["IIIF_SIMPLE_PREVIEWER_SIZE"]
        tpl_ctx["iiif_simple_url"] = (
            f"{file.data['links']['iiif_base']}/full/{size}/0/default.{format}"
        )

        # Add banner message if needed
        if record.is_draft:
            tpl_ctx["banner_message"] = "Zoom is not available in Preview"
        elif tile_status in ("init", "processing"):
            tpl_ctx["banner_message"] = (
                "Zoom will be available shortly (processing in progress)"
            )

    return render_template(
        "invenio_app_rdm/records/mirador_preview.html",
        css_bundles=["mirador-previewer.css"],
        file=file,
        **tpl_ctx,
    )
