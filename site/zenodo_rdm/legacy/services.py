# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy services."""

from copy import deepcopy
from os.path import splitext

from flask import current_app
from invenio_app_rdm.records_ui.previewer.iiif_simple import (
    previewable_extensions as image_extensions,
)
from invenio_db import db
from invenio_drafts_resources.services.records.config import is_record
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.proxies import current_record_communities_service
from invenio_rdm_records.records import RDMRecord
from invenio_rdm_records.services import (
    RDMFileDraftServiceConfig,
    RDMRecordService,
    RDMRecordServiceConfig,
)
from invenio_rdm_records.services.config import has_doi
from invenio_records_resources.services import ConditionalLink
from invenio_records_resources.services.base.config import FromConfig
from invenio_records_resources.services.base.links import preprocess_vars
from invenio_records_resources.services.errors import FileKeyNotFoundError
from invenio_records_resources.services.files import FileLink, FileService
from invenio_records_resources.services.records.links import RecordLink
from invenio_records_resources.services.uow import (
    IndexRefreshOp,
    RecordCommitOp,
    unit_of_work,
)
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

record_thumbnail_sizes = LocalProxy(
    lambda: current_app.config["APP_RDM_RECORD_THUMBNAIL_SIZES"]
)
"""Proxy for the config variable for the available record thumbnail sizes."""


def is_published(record, ctx):
    """True if the record/draft is published."""
    return record.is_published


def is_record_and_has_parent_doi(record, ctx):
    """Determine if record has parent doi."""
    return is_record(record, ctx) and has_doi(record.parent, ctx)


class LegacyRecordLink(RecordLink):
    """Legacy record links with bucket information."""

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        vars.update(
            {
                "id": record.pid.pid_value,
                "bucket_id": record.bucket_id,
            }
        )


class LegacyThumbsLink(RecordLink):
    """Legacy thumbnail links dictionary."""

    def __init__(self, *args, sizes=None, **kwargs):
        """Constructor."""
        self._sizes = sizes
        super().__init__(*args, **kwargs)

    def expand(self, obj, context):
        """Expand the thumbs size dictionary of URIs."""
        vars = {}
        vars.update(deepcopy(context))
        self.vars(obj, vars)
        if self._vars_func:
            self._vars_func(obj, vars)
        vars = preprocess_vars(vars)
        return {str(s): self._uritemplate.expand(size=s, **vars) for s in self._sizes}


def is_iiif_compatible(record, ctx):
    """Check if a record is IIIF compatible, i.e. if it has compatible image files."""
    for f in record.files.entries:
        f_ext = splitext(f)[1].replace(".", "").lower()
        if f_ext in image_extensions:
            return True
    return False


class RecordPIDLink(RecordLink):
    """Record PID links."""

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        vars.update(
            {f"pid_{scheme}": pid["identifier"] for scheme, pid in record.pids.items()}
        )


class RecordParentPIDLink(RecordLink):
    """Record parent PID links."""

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        vars.update(
            {
                f"pid_{scheme}": pid["identifier"]
                for scheme, pid in record.parent.pids.items()
            }
        )


class LegacyRecordServiceConfig(RDMRecordServiceConfig):
    """Legacy record service config."""

    links_item = {
        "self": ConditionalLink(
            cond=is_record,
            if_=RecordLink("{+api}/records/{id}"),
            else_=RecordLink("{+api}/deposit/depositions/{id}"),
        ),
        "html": ConditionalLink(
            cond=is_record,
            if_=RecordLink("{+ui}/records/{id}"),
            else_=RecordLink("{+ui}/deposit/{id}"),
        ),
        "doi": RecordPIDLink("https://doi.org/{+pid_doi}", when=has_doi),
        "parent_doi": RecordParentPIDLink(
            "{+ui}/doi/{+pid_doi}",
            when=is_record_and_has_parent_doi,
        ),
        "badge": RecordPIDLink("{+ui}/badge/doi/{pid_doi}.svg"),
        "conceptbadge": RecordParentPIDLink(
            "{+ui}/badge/doi/{pid_doi}.svg",
            when=is_record_and_has_parent_doi,
        ),
        #
        # Files
        #
        "files": ConditionalLink(
            cond=is_record,
            if_=RecordLink("{+api}/records/{id}/files"),
            else_=RecordLink("{+api}/deposit/depositions/{id}/files"),
        ),
        "bucket": LegacyRecordLink("{+api}/files/{bucket_id}"),
        #
        # Thumbnails
        #
        "thumb250": RecordLink("{+ui}/record/{id}/thumb250", when=is_iiif_compatible),
        "thumbs": LegacyThumbsLink(
            "{+ui}/record/{id}/thumb{size}",
            when=is_iiif_compatible,
            sizes=record_thumbnail_sizes,
        ),
        # Versioning
        "latest_draft": RecordLink("{+api}/deposit/depositions/{id}"),
        "latest_draft_html": RecordLink("{+ui}/deposit/{id}"),
        #
        # Actions
        #
        "publish": RecordLink("{+api}/deposit/depositions/{id}/actions/publish"),
        "edit": RecordLink("{+api}/deposit/depositions/{id}/actions/edit"),
        "discard": RecordLink("{+api}/deposit/depositions/{id}/actions/discard"),
        "newversion": RecordLink("{+api}/deposit/depositions/{id}/actions/newversion"),
        "registerconceptdoi": RecordLink(
            "{+api}/deposit/depositions/{id}/actions/registerconceptdoi"
        ),
        #
        # Published draft
        #
        "record": RecordLink("{+api}/records/{id}", when=is_published),
        "record_html": RecordLink("{+ui}/record/{id}", when=is_published),
        "latest": RecordLink("{+api}/records/{id}/versions/latest", when=is_published),
        "latest_html": RecordLink(
            "{+ui}/record/{id}/versions/latest", when=is_published
        ),
    }


class LegacyRecordService(RDMRecordService):
    """Legacy record service."""

    def read_draft(self, identity, id_, expand=False):
        """Retrieve a draft."""
        try:
            # Try first the draft
            draft = self.draft_cls.pid.resolve(id_, registered_only=False)
        except NoResultFound:
            # If it's published try the record
            draft = self.record_cls.pid.resolve(id_, registered_only=True)
        self.require_permission(identity, "read_draft", record=draft)

        # Run components
        for component in self.components:
            if hasattr(component, "read_draft"):
                component.read_draft(identity, draft=draft)

        return self.result_item(
            self,
            identity,
            draft,
            links_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )

    @unit_of_work()
    def publish(self, identity, id_, uow=None, expand=False):
        """Publish a draft."""
        res = super().publish(identity, id_, uow=uow, expand=expand)
        record = res._record

        # Deal with communities
        communities = record.get("custom_fields", {}).pop("legacy:communities", [])

        community_ops = []
        # TODO: Check if we need to actually remove communities
        for community_id in communities:
            try:
                community_ops.append(
                    current_record_communities_service._include(
                        identity,
                        community_id,
                        comment=None,
                        require_review=False,
                        record=record,
                        uow=uow,
                    )
                )
            # TODO: See if we can narrow down what exceptions we want to handle
            except Exception:
                pass
        if community_ops:
            uow.register(RecordCommitOp(record, indexer=self.indexer))
            uow.register(IndexRefreshOp(indexer=self.indexer))

        return res


class LegacyFileLink(FileLink):
    """Legacy file link."""

    @staticmethod
    def vars(file_record, vars):
        """Variables for the URI template."""
        vars.update(
            {
                "key": file_record.key,
                "bucket_id": file_record.record.bucket_id,
                "version_id": file_record.object_version_id,
                "file_id": file_record.file.id,
            }
        )


class LegacyFileDraftServiceConfig(RDMFileDraftServiceConfig):
    """Configuration for legacy draft files."""

    service_id = "legacy-draft-files"

    published_record_cls = FromConfig("RDM_RECORD_CLS", default=RDMRecord)

    file_links_list = {
        "self": RecordLink("{+api}/deposit/depositions/{id}/files"),
    }

    file_links_item = {
        "draft_files.self": LegacyFileLink(
            "{+api}/deposit/depositions/{id}/files/{file_id}"
        ),
        "draft_files.download": LegacyFileLink("{+api}/files/{bucket_id}/files/{key}"),
        "files_rest.self": LegacyFileLink("{+api}/files/{bucket_id}/files/{key}"),
        "files_rest.version": LegacyFileLink(
            "{+api}/files/{bucket_id}/files/{key}?versionId={version_id}"
        ),
        "files_rest.uploads": LegacyFileLink(
            "{+api}/files/{bucket_id}/files/{key}?uploads"
        ),
    }


class LegacyFileService(FileService):
    """Legacy files service."""

    def _get_record(self, id_, identity, action, file_key=None):
        """Get the associated record.

        Adds support for getting a draft or a record instead of only draft.
        Needed for legacy API compatibility.
        """
        try:
            # Try first the draft
            record = self.record_cls.pid.resolve(id_, registered_only=False)
        except NoResultFound:
            # If it's published try the record
            record = self.config.published_record_cls.pid.resolve(
                id_, registered_only=True
            )
        self.require_permission(identity, action, record=record, file_key=file_key)

        if file_key and file_key not in record.files:
            raise FileKeyNotFoundError(id_, file_key)

        return record

    def get_record_by_bucket_id(self, bucket_id):
        """Get the associated record by its bucket ID."""
        try:
            # Try first the draft
            model_cls = self.record_cls.model_cls
            obj = model_cls.query.filter(model_cls.bucket_id == bucket_id).one()
            return self.record_cls(obj.data, model=obj)
        except NoResultFound:
            # If it's published try the record
            model_cls = self.config.published_record_cls.model_cls
            obj = model_cls.query.filter(model_cls.bucket_id == bucket_id).one()
            return self.config.published_record_cls(obj.data, model=obj)

    def get_file_key_by_id(self, pid_value, file_id):
        """Get the associated record file key by its ID."""
        RDMDraft = self.record_cls.model_cls
        key = (
            db.session.query(ObjectVersion.key)
            .join(FileInstance, ObjectVersion.file_id == FileInstance.id)
            .join(RDMDraft, ObjectVersion.bucket_id == RDMDraft.bucket_id)
            .join(PersistentIdentifier, PersistentIdentifier.object_uuid == RDMDraft.id)
            .filter(
                FileInstance.id == file_id,
                PersistentIdentifier.pid_type == "recid",
                PersistentIdentifier.pid_value == pid_value,
                PersistentIdentifier.object_type == "rec",
            )
            .scalar()
        )
        return key
