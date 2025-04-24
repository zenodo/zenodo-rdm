# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy API."""

from flask_principal import identity_loaded
from invenio_rdm_records.services.pids import PIDManager, PIDsService
from invenio_rdm_records.services.review.service import ReviewService

from .resources import (
    LegacyDraftFilesResource,
    LegacyDraftFilesResourceConfig,
    LegacyFilesRESTResource,
    LegacyFilesRESTResourceConfig,
    LegacyRecordResource,
    LegacyRecordResourceConfig,
)
from .services import (
    LegacyFileDraftServiceConfig,
    LegacyFileService,
    LegacyRecordService,
    LegacyRecordServiceConfig,
)
from .tokens import verify_legacy_secret_link


@identity_loaded.connect
def on_identity_loaded(_, identity):
    """Add legacy secret link token to the freshly loaded Identity."""
    verify_legacy_secret_link(identity)


class ZenodoLegacy:
    """Zenodo legacy compatibility extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_services(app)
        self.init_resource(app)
        app.extensions["zenodo-rdm-legacy"] = self

    def service_configs(self, app):
        """Customized service configs."""

        class ServiceConfigs:
            record = LegacyRecordServiceConfig.build(app)
            file_draft = LegacyFileDraftServiceConfig.build(app)

        return ServiceConfigs

    def init_services(self, app):
        """Initialize services."""
        service_configs = self.service_configs(app)

        # Services
        self.legacy_records_service = LegacyRecordService(
            service_configs.record,
            draft_files_service=LegacyFileService(service_configs.file_draft),
            # NOTE: Not needed probably
            # secret_links_service=SecretLinkService(service_configs.record),
            pids_service=PIDsService(service_configs.record, PIDManager),
            # NOTE: Note needed yet, but will have to bypass when we do communities
            review_service=ReviewService(service_configs.record),
        )

    def init_resource(self, app):
        """Initialize resources."""
        self.legacy_records_resource = LegacyRecordResource(
            LegacyRecordResourceConfig.build(app),
            self.legacy_records_service,
        )

        # Draft files resource
        self.legacy_draft_files_resource = LegacyDraftFilesResource(
            service=self.legacy_records_service.draft_files,
            config=LegacyDraftFilesResourceConfig,
        )

        # Files-REST resource
        self.legacy_files_rest_resource = LegacyFilesRESTResource(
            service=self.legacy_records_service.draft_files,
            config=LegacyFilesRESTResourceConfig,
        )


def register_services(app):
    """Register the legacy services (to be used in ``invenio_base.finalize_app``)."""
    sregistry = app.extensions["invenio-records-resources"].registry
    ext = app.extensions["zenodo-rdm-legacy"]
    sregistry.register(ext.legacy_records_service, service_id="legacy-records")
    sregistry.register(
        ext.legacy_records_service.draft_files, service_id="legacy-draft-files"
    )
