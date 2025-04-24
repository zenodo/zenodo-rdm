# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy views."""

from .resources import (
    DraftExtraFormatsResource,
    DraftExtraFormatsResourceConfig,
    RecordExtraFormatsResource,
    RecordExtraFormatsResourceConfig,
)


def create_legacy_records_bp(app):
    """Create legacy records blueprint."""
    ext = app.extensions["zenodo-rdm-legacy"]
    return ext.legacy_records_resource.as_blueprint()


def create_draft_files_bp(app):
    """Create legacy draft files blueprint."""
    ext = app.extensions["zenodo-rdm-legacy"]
    return ext.legacy_draft_files_resource.as_blueprint()


def create_files_rest_bp(app):
    """Create legacy Files-REST blueprint."""
    ext = app.extensions["zenodo-rdm-legacy"]
    return ext.legacy_files_rest_resource.as_blueprint()


def create_legacy_draft_extra_formats_bp(app):
    """Create legacy draft extra formats blueprint."""
    records_ext = app.extensions["invenio-rdm-records"]

    legacy_draft_extra_formats_resource = DraftExtraFormatsResource(
        # NOTE: We pass the top-level record service, since we need to handle cases when
        # extra formats are modified on a published draft.
        service=records_ext.records_media_files_service,
        config=DraftExtraFormatsResourceConfig.build(app),
    )
    return legacy_draft_extra_formats_resource.as_blueprint()


def create_legacy_record_extra_formats_bp(app):
    """Create legacy record extra formats blueprint."""
    records_ext = app.extensions["invenio-rdm-records"]

    legacy_record_extra_formats_resource = RecordExtraFormatsResource(
        service=records_ext.records_media_files_service,
        config=RecordExtraFormatsResourceConfig.build(app),
    )
    return legacy_record_extra_formats_resource.as_blueprint()
