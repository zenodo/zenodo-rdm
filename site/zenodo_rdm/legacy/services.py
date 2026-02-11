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
from invenio_base.urls import invenio_url_for
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
from invenio_rdm_records.services.config import RecordPIDLink, WithFileLinks, has_doi
from invenio_records_resources.services import ConditionalLink
from invenio_records_resources.services.base.config import FromConfig
from invenio_records_resources.services.errors import FileKeyNotFoundError
from invenio_records_resources.services.files import FileService
from invenio_records_resources.services.files.links import FileEndpointLink
from invenio_records_resources.services.records.links import RecordEndpointLink
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


def is_published_file(file, ctx):
    """Determine if file belongs to a record/draft."""
    return not file.record.is_draft


class LegacyRecordEndpointLink(RecordEndpointLink):
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


class LegacyThumbsLink(RecordEndpointLink):
    """Legacy thumbnail links dictionary."""

    def __init__(self, *args, sizes, **kwargs):
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

        # Filter out vars that are not in the params
        values = {k: v for k, v in vars.items() if k in self._params}

        # Add any querystring arguments
        values.update(vars.get("args", {}))
        values = dict(sorted(values.items()))  # keep sorted interface
        return {
            str(s): invenio_url_for(self._endpoint, size=s, **values)
            for s in self._sizes
        }


def is_iiif_compatible(record, ctx):
    """Check if a record is IIIF compatible, i.e. if it has compatible image files."""
    for f in record.files.entries:
        f_ext = splitext(f)[1].replace(".", "").lower()
        if f_ext in image_extensions:
            return True
    return False


def has_bucket_id(record, ctx):
    """Check if record has bucket_id.

    This is needed because we don't index the bucket_id information.
    """
    return getattr(record, "bucket_id") is not None


def has_file(file_record, ctx):
    """Check if record has bucket_id.

    This is needed because we don't index the bucket_id information.
    """
    return getattr(file_record, "file") is not None


class LegacyRecordServiceConfig(RDMRecordServiceConfig):
    """Legacy record service config."""

    links_item = {
        "self": ConditionalLink(
            cond=is_record,
            if_=RecordEndpointLink("records.read"),
            else_=RecordEndpointLink("legacy_records.read_draft"),
        ),
        "html": ConditionalLink(
            cond=is_record,
            if_=RecordEndpointLink("invenio_app_rdm_records.record_detail"),
            else_=RecordEndpointLink("invenio_redirector.redirect_deposit_id"),
        ),
        "doi": RecordPIDLink("https://doi.org/{+pid_doi}", when=has_doi),
        "parent_doi": RecordPIDLink(
            "https://doi.org/{+parent_pid_doi}",
            when=is_record_and_has_parent_doi,
        ),
        "badge": RecordPIDLink("{+ui}/badge/doi/{pid_doi}.svg"),
        "conceptbadge": RecordPIDLink(
            "{+ui}/badge/doi/{parent_pid_doi}.svg",
            when=is_record_and_has_parent_doi,
        ),
        #
        # Files
        #
        "files": ConditionalLink(
            cond=is_record,
            if_=RecordEndpointLink("record_files.search"),
            else_=RecordEndpointLink("legacy_draft_files.search"),
        ),
        "bucket": LegacyRecordEndpointLink(
            "legacy_files_rest.search", params=["bucket_id"], when=has_bucket_id
        ),
        #
        # Thumbnails
        #
        "thumb250": RecordEndpointLink(
            "invenio_redirector.redirect_record_thumbnail",
            vars=lambda _, v: v.update({"size": "250"}),
            params=["pid_value", "size"],
            when=is_iiif_compatible,
        ),
        "thumbs": LegacyThumbsLink(
            "invenio_redirector.redirect_record_thumbnail",
            sizes=record_thumbnail_sizes,
            when=is_iiif_compatible,
        ),
        # Versioning
        "latest_draft": RecordEndpointLink("legacy_records.read_draft"),
        "latest_draft_html": RecordEndpointLink(
            "invenio_redirector.redirect_deposit_id"
        ),
        #
        # Actions
        #
        "publish": RecordEndpointLink("legacy_records.publish"),
        "edit": RecordEndpointLink("legacy_records.edit"),
        "discard": RecordEndpointLink("legacy_records.discard_draft"),
        "newversion": RecordEndpointLink("legacy_records.new_version"),
        # TODO: Implement this
        # "registerconceptdoi": RecordEndpointLink("legacy_records.register_concept_doi"),
        #
        # Published draft
        #
        "record": RecordEndpointLink("records.read", when=is_published),
        "record_html": RecordEndpointLink(
            "invenio_redirector.redirect_record_detail", when=is_published
        ),
        "latest": RecordEndpointLink("records.read_latest", when=is_published),
        "latest_html": RecordEndpointLink(
            "invenio_app_rdm_records.record_latest", when=is_published
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


class LegacyFileLink(FileEndpointLink):
    """Legacy file link."""

    @staticmethod
    def vars(file_record, vars):
        """Variables for the URI template."""
        vars.update(
            {
                "key": file_record.key,
                "bucket_id": file_record.record.bucket_id,
                "file_id": file_record.file.id if file_record.file else None,
            }
        )


class IngoreFileLinkMeta(WithFileLinks):
    """Metaclass to ignore the existing WithFileLinks base class."""

    def __init__(cls, *args, **kwargs):
        """Ignore the WithFileLinks base class."""
        # Do nothing, we'll handle links ourselves
        pass


class LegacyFileDraftServiceConfig(
    RDMFileDraftServiceConfig, metaclass=IngoreFileLinkMeta
):
    """Configuration for legacy draft files."""

    service_id = "legacy-draft-files"

    published_record_cls = FromConfig("RDM_RECORD_CLS", default=RDMRecord)

    file_links_list = {
        "self": RecordEndpointLink("legacy_draft_files.search"),
    }

    file_links_item = {
        "draft_files.self": LegacyFileLink(
            "legacy_draft_files.read",
            params=["pid_value", "file_id"],
            when=has_file,
        ),
        "draft_files.download": ConditionalLink(
            cond=is_published_file,
            if_=LegacyFileLink(
                "record_files.read_content",
                params=["pid_value", "key"],
                when=has_file,
            ),
            else_=LegacyFileLink(
                "draft_files.read_content",
                params=["pid_value", "key"],
                when=has_file,
            ),
        ),
        "files_rest.self": LegacyFileLink(
            "legacy_files_rest.get_object",
            params=["bucket_id", "key"],
            when=has_file,
        ),
        "files_rest.version": LegacyFileLink(
            "legacy_files_rest.get_object",
            params=["bucket_id", "key"],
            vars=lambda o, v: v.update({"args": {"version_id": o.object_version_id}}),
            when=has_file,
        ),
        "files_rest.uploads": LegacyFileLink(
            "legacy_files_rest.get_object",
            params=["bucket_id", "key"],
            vars=lambda o, v: v.update({"args": {"uploads": "1"}}),
            when=has_file,
        ),
    }


class LegacyFileService(FileService):
    """Legacy files service."""

    def check_permission(self, identity, action_name, **kwargs):
        """Check permission with an optional per-call action prefix."""
        prefix = kwargs.pop(
            "permission_action_prefix",
            self.config.permission_action_prefix,
        )
        return self.permission_policy(f"{prefix}{action_name}", **kwargs).allows(
            identity
        )

    def _get_record(self, id_, identity, action, file_key=None):
        """Get the associated record.

        Adds support for getting a draft or a record instead of only draft.
        Needed for legacy API compatibility.
        """
        permission_action_prefix = "draft_"
        try:
            # Try first the draft
            record = self.record_cls.pid.resolve(id_, registered_only=False)
        except NoResultFound:
            # If it's published try the record
            record = self.config.published_record_cls.pid.resolve(
                id_, registered_only=True
            )
            permission_action_prefix = ""

        self.require_permission(
            identity,
            action,
            record=record,
            file_key=file_key,
            permission_action_prefix=permission_action_prefix,
        )

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

        def query_file_id_by_model_cls(model_cls):
            """Query for file based on passed model cls."""
            key = (
                db.session.query(ObjectVersion.key)
                .join(FileInstance, ObjectVersion.file_id == FileInstance.id)
                .join(model_cls, ObjectVersion.bucket_id == model_cls.bucket_id)
                .join(
                    PersistentIdentifier,
                    PersistentIdentifier.object_uuid == model_cls.id,
                )
                .filter(
                    FileInstance.id == file_id,
                    PersistentIdentifier.pid_type == "recid",
                    PersistentIdentifier.pid_value == pid_value,
                    PersistentIdentifier.object_type == "rec",
                )
                .scalar()
            )
            return key

        RDMDraft = self.record_cls.model_cls
        key = query_file_id_by_model_cls(RDMDraft)
        if key is None:
            RDMRecord = self.config.published_record_cls.model_cls
            key = query_file_id_by_model_cls(RDMRecord)
        return key
