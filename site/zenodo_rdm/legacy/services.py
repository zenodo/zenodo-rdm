# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy services."""

from invenio_drafts_resources.services.records.config import is_draft, is_record
from invenio_rdm_records.proxies import current_record_communities_service
from invenio_rdm_records.services import (
    RDMFileDraftServiceConfig,
    RDMRecordService,
    RDMRecordServiceConfig,
)
from invenio_rdm_records.services.config import has_doi, is_record_and_has_parent_doi
from invenio_records_resources.services import ConditionalLink
from invenio_records_resources.services.files import FileLink, FileService
from invenio_records_resources.services.records.links import RecordLink
from invenio_records_resources.services.uow import (
    IndexRefreshOp,
    RecordCommitOp,
    unit_of_work,
)
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

def is_published(record, ctx):
    """True if the record/draft is published."""
    return record.is_published


class LegacyRecordLink(RecordLink):
    """Short cut for writing record links."""

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        vars.update(
            {
                "id": record.pid.pid_value,
                "bucket_id": record.bucket_id,
            }
        )




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

    @unit_of_work()
    def create(self, identity, data, uow=None, expand=False):
        """Create a draft and prereserve the DOI."""
        res = super().create(identity, data, uow=uow, expand=False)


        return res

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
        # TODO: Check if user is owner/curator of all the communities (i.e. auto-accept)
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
            }
        )


class LegacyFileDraftServiceConfig(RDMFileDraftServiceConfig):
    """Configuration for legacy draft files."""

    service_id = "legacy-draft-files"

    file_links_list = {
        "self": RecordLink("{+api}/deposit/depositions/{id}/files"),
    }

    file_links_item = {
        "self": LegacyFileLink("{+api}/deposit/depositions/{id}/files/{key}"),
    }


class LegacyFileService(FileService):
    """Legacy files service."""

    def get_record_by_bucket_id(self, bucket_id):
        """Get the associated record by its bucket ID."""
        model_cls = self.record_cls.model_cls
        obj = model_cls.query.filter(model_cls.bucket_id == bucket_id).one()
        return self.record_cls(obj.data, model=obj)
