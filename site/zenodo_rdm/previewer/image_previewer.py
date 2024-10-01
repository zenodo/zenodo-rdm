# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Image previewer."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from os.path import splitext

from flask import current_app, render_template


def is_pdf_previewable(file):
    """Check if the file is a PDF that should be previewed."""
    return (
        file.has_extensions(".pdf")
        and file.data.get("metadata", {}).get("previewer", "") == "image_previewer"
        and bool(file.record._record.media_files.entries)
    )


def can_preview(file):
    """Check if file can be previewed by this previewer.

    :param file: The file to be previewed.
    :returns: Boolean.
    """
    # supported_extensions list for image formats
    preview_extensions = current_app.config["IIIF_FORMATS"]
    supported_extensions = ["." + ext for ext in preview_extensions if ext != "pdf"]

    if is_pdf_previewable(file):
        return True

    if file.has_extensions(*supported_extensions):
        return True

    return False


def preview(file):
    """Render template."""
    record = file.record._record
    tpl_ctx = {}
    iiif_config = current_app.config["IIIF_TILES_CONVERTER_PARAMS"]

    # Check the status of the tile generation for the image
    tile_status = None
    if record.media_files.enabled and not record.is_draft:
        tile_file = record.media_files.get(f"{file.filename}.ptif")
        if tile_file is not None and tile_file.processor:
            tile_status = tile_file.processor.get("status")

    if not file.has_extensions(".pdf"):
        # Check if the file was updated more than an hour ago
        last_updated_time = datetime.fromisoformat(file.data["updated"])
        current_time = datetime.now(timezone.utc)
        time_diff = current_time - last_updated_time
        threshold_time = timedelta(
            **current_app.config["PREVIEWER_IMAGE_FAILED_PROCESSING_TIMEDELTA"]
        )

        # If the image tile status size is processing and the image was last updated more than an hour ago
        if tile_status == "processing" and time_diff > threshold_time:
            # The image size is less than configured size, fall back to IIIF
            if file.size < current_app.config["PREVIEWER_MAX_IMAGE_SIZE_BYTES"]:
                return render_template(
                    "invenio_app_rdm/records/previewers/simple_image_preview.html",
                    css_bundles=["image-previewer.css"],
                    file_url=file.file.links["iiif_api"],
                )
            # The image size is greater than configured size,
            # image cannot be previewed
            elif file.size > current_app.config["PREVIEWER_MAX_IMAGE_SIZE_BYTES"]:
                return render_template(
                    "invenio_app_rdm/records/previewers/preview_unavailable.html",
                    css_bundles=current_app.config[
                        "PREVIEWER_BASE_CSS_BUNDLES"
                    ]  # Basic bundle which includes Font-Awesome/Bootstrap
                    + ["image-previewer.css"],
                    file=file,
                )
        else:
            metadata = file.data.get("metadata")
            width = metadata.get("width") if metadata else None
            height = metadata.get("height") if metadata else None

            # If metadata is missing, or if width or height are missing or smaller than the configured tile size
            if (
                not metadata
                or not (width and height)
                or width <= iiif_config["tile_width"]
                or height <= iiif_config["tile_height"]
            ):
                return render_template(
                    "invenio_app_rdm/records/previewers/simple_image_preview.html",
                    css_bundles=["image-previewer.css"],
                    file_url=file.uri,
                )

    supported_mirador_extensions = [
        "." + ext for ext in current_app.config["MIRADOR_PREVIEW_EXTENSIONS"]
    ]
    show_mirador = tile_status == "finished" and file.has_extensions(
        *supported_mirador_extensions
    )
    tpl_ctx["show_mirador"] = show_mirador

    if show_mirador:
        # Add IIIF URLs for Mirador
        if not is_pdf_previewable(file):
            tpl_ctx["iiif_canvas_url"] = file.data["links"]["iiif_canvas"]
        tpl_ctx["iiif_manifest_url"] = file.record["links"]["self_iiif_manifest"]
        tpl_ctx["mirador_cfg"] = deepcopy(current_app.config["MIRADOR_PREVIEW_CONFIG"])

        # Generate dictionary of annotation files
        annotations = {}

        # Iterate through both record.files and record.media_files
        for file_list, base_url in [
            (record.files, "files"),
            (record.media_files, "media_files"),
        ]:
            for filename in file_list:
                if filename.endswith(".wadm"):
                    main_filename = filename[:-5]  # Remove the ".wadm" part
                    # Check if the main file exists in either files or media_files
                    if (
                        main_filename in record.files
                        or main_filename in record.media_files
                    ):
                        annotations[main_filename] = (
                            f"{file.record['links'][base_url]}/{filename}/content"
                        )

        tpl_ctx["annotations"] = annotations

        tpl_ctx["mirador_cfg"]["window"]["panels"]["annotations"] = bool(annotations)
        tpl_ctx["mirador_cfg"]["window"]["sideBarOpen"] = bool(annotations)
        tpl_ctx["mirador_cfg"]["window"]["sideBarPanel"] = (
            "annotations" if annotations else "info"
        )

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
        "invenio_app_rdm/records/previewers/mirador_preview.html",
        css_bundles=["image-previewer.css"],
        file=file,
        **tpl_ctx,
    )
