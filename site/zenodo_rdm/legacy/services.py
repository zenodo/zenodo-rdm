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
from invenio_records_resources.services import ConditionalLink
from invenio_records_resources.services.files import FileLink, FileService
from invenio_records_resources.services.records.links import RecordLink
from invenio_records_resources.services.uow import IndexRefreshOp, unit_of_work


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
        # Versioning
        #
        # TODO: Pass latest versioning IDs
        # "latest_draft": RecordLink("{+api}/deposit/depositions/{id}", when=is_draft),
        # "latest_draft_html": RecordLink("{+ui}/deposit/{id}", when=is_draft),
        #
        # Actions
        #
        "publish": RecordLink(
            "{+api}/deposit/depositions/{id}/actions/publish", when=is_draft
        ),
        "edit": RecordLink(
            "{+api}/deposit/depositions/{id}/actions/edit", when=is_draft
        ),
        "discard": RecordLink(
            "{+api}/deposit/depositions/{id}/actions/discard", when=is_draft
        ),
    }


class LegacyRecordService(RDMRecordService):
    """Legacy record service."""

    @unit_of_work()
    def create(self, identity, data, uow=None, expand=False):
        """Create a draft and prereserve the DOI."""
        res = super().create(identity, data, uow=uow, expand=False)
        res = self.pids.create(
            identity=identity,
            id_=res.id,
            scheme="doi",
            expand=True,
            uow=uow,
        )
        communities = data.get("communities", [])
        p = self.add_communities(communities, identity, uow, res._record)

        # TODO how
        # uow.register(IndexRefreshOp(indexer=current_record_communities_service.indexer))

        return res

    def add_communities(self, communities, identity, uow, record):
        """Creates community inclusion requests for a record's communities.

        This bypasses the record communities service checks on community add.
        """
        if not communities:
            return

        processed = []
        errored = []
        for community in communities:
            community_id = community["id"]
            comment = community.get("comment", None)
            require_review = community.get("require_review", False)

            result = {
                "community_id": community_id,
            }
            try:
                request_item = current_record_communities_service._include(
                    identity, community_id, comment, require_review, record, uow
                )
                result["request_id"] = str(request_item.data["id"])
                result["request"] = request_item.to_dict()
                processed.append(result)
            except Exception as e:
                errored.append(e)
                raise e
        return processed


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
