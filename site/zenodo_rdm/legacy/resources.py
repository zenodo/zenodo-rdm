# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy resources."""

import copy
from functools import wraps

import marshmallow as ma
from flask import abort, g, request
from flask_resources import (
    RequestBodyParser,
    ResponseHandler,
    request_parser,
    resource_requestctx,
    response_handler,
    route,
)
from invenio_rdm_records.resources.config import (
    RDMDraftFilesResourceConfig,
    RDMRecordResourceConfig,
)
from invenio_rdm_records.resources.config import (
    record_serializers as default_record_serializers,
)
from invenio_rdm_records.resources.resources import RDMRecordResource
from invenio_records_resources.resources.files.resource import (
    FileResource,
    request_stream,
    request_view_args,
)
from invenio_records_resources.resources.records.headers import etag_headers
from invenio_records_resources.services.errors import FileKeyNotFoundError
from invenio_records_resources.services.uow import UnitOfWork
from werkzeug.utils import secure_filename

from .deserializers import LegacyJSONDeserializer
from .serializers import (
    LegacyDraftFileJSONSerializer,
    LegacyFilesRESTJSONSerializer,
    LegacyJSONSerializer,
    ZenodoJSONSerializer,
)

record_serializers = copy.deepcopy(default_record_serializers)
record_serializers.update(
    {
        "application/json": ResponseHandler(
            ZenodoJSONSerializer(), headers=etag_headers
        ),
        "application/vnd.zenodo.v1+json": ResponseHandler(
            ZenodoJSONSerializer(), headers=etag_headers
        ),
        # Alias for the DataCite XML serializer
        "application/x-datacite+xml": record_serializers[
            "application/vnd.datacite.datacite+xml"
        ],
    }
)


class LegacyRecordResourceConfig(RDMRecordResourceConfig):
    """Legacy record resource config."""

    blueprint_name = "legacy_records"
    url_prefix = "/deposit/depositions"

    request_body_parsers = {
        "application/json": RequestBodyParser(LegacyJSONDeserializer()),
    }

    response_handlers = {
        "application/json": ResponseHandler(
            LegacyJSONSerializer(), headers=etag_headers
        ),
    }

    routes = {
        "list": "",
        "item-draft": "/<pid_value>",
        "item-publish": "/<pid_value>/actions/publish",
        "item-edit": "/<pid_value>/actions/edit",
        "item-discard": "/<pid_value>/actions/discard",
        "item-newversion": "/<pid_value>/actions/newversion",
    }


class LegacyRecordResource(RDMRecordResource):
    """Legacy record resource."""

    def create_url_rules(self):
        """Create the URL rules for the record resource."""

        def p(route):
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        routes = self.config.routes
        url_rules = [
            route("GET", p(routes["list"]), self.search_user_records),
            route("POST", p(routes["list"]), self.create),
            route("GET", p(routes["item-draft"]), self.read_draft),
            route("PUT", p(routes["item-draft"]), self.update_draft),
            route("DELETE", p(routes["item-draft"]), self.delete_draft),
            route("POST", p(routes["item-publish"]), self.publish),
            route("POST", p(routes["item-edit"]), self.edit),
            # TODO: check differences from plain DELETE
            route(
                "POST",
                p(routes["item-discard"]),
                self.delete_draft,
                endpoint="discard_draft",
            ),
            # We override, since we want to automatically import the files
            route("POST", p(routes["item-newversion"]), self.new_version),
        ]
        return url_rules

    @request_view_args
    @response_handler()
    def new_version(self):
        """Create a new version and import files."""
        with UnitOfWork() as uow:
            new_version_item = self.service.new_version(
                g.identity,
                resource_requestctx.view_args["pid_value"],
                uow=uow,
            )
            self.service.import_files(g.identity, new_version_item.id, uow=uow)
            uow.commit()

        # Fetch the latest version and return it
        # TODO: We could maybe just return `new_version_item`?
        item = self.service.read_draft(g.identity, new_version_item.id)
        return item.to_dict(), 201


class LegacyDraftFilesResourceConfig(RDMDraftFilesResourceConfig):
    """Legacy draft files resource config."""

    blueprint_name = "legacy_draft_files"
    url_prefix = "/deposit/depositions"

    response_handlers = {
        "application/json": ResponseHandler(
            LegacyDraftFileJSONSerializer(), headers=etag_headers
        ),
    }

    routes = {
        "list": "/<pid_value>/files",
        "item": "/<pid_value>/files/<file_id>",
    }


def request_files_body(f):
    """Request parser for multipart/form-data files and data."""

    @wraps(f)
    def inner(self, *args, **kwargs):
        resource_requestctx.data = {
            "request_data": request.form,
            "request_files": request.files,
        }
        return f(self, *args, **kwargs)

    return inner


request_draft_files_view_args = request_parser(
    {"pid_value": ma.fields.Str(required=True), "file_id": ma.fields.Str()},
    location="view_args",
)


class LegacyDraftFilesResource(FileResource):
    """Legacy draft files resource."""

    def create_url_rules(self):
        """Create the URL rules for the draft files resource."""
        routes = self.config.routes
        url_rules = [
            # Old-style API
            route("GET", routes["list"], self.search),
            route("POST", routes["list"], self.create),
            route("GET", routes["item"], self.read),
            route("DELETE", routes["item"], self.delete),
        ]

        return url_rules

    @request_view_args
    @request_files_body
    @response_handler()
    def create(self):
        """Upload a file using multipart/form-data."""
        pid_value = resource_requestctx.view_args["pid_value"]
        file = resource_requestctx.data["request_files"]["file"]
        key = secure_filename(
            resource_requestctx.data["request_data"].get("name", file.filename)
        )

        with UnitOfWork() as uow:
            self.service.init_files(g.identity, pid_value, [{"key": key}], uow=uow)
            self.service.set_file_content(g.identity, pid_value, key, file, uow=uow)
            item = self.service.commit_file(g.identity, pid_value, key, uow=uow)
            uow.commit()

        return item.to_dict(), 201

    @request_draft_files_view_args
    @response_handler()
    def read(self):
        """Read a single file."""
        pid_value = resource_requestctx.view_args["pid_value"]
        file_id = resource_requestctx.view_args["file_id"]
        key = self.service.get_file_key_by_id(pid_value, file_id)
        if key is None:
            abort(404)
        item = self.service.read_file_metadata(g.identity, pid_value, key)
        return item.to_dict(), 200

    @request_draft_files_view_args
    def delete(self):
        """Delete a file."""
        pid_value = resource_requestctx.view_args["pid_value"]
        file_id = resource_requestctx.view_args["file_id"]
        key = self.service.get_file_key_by_id(pid_value, file_id)
        if key is None:
            abort(404)
        self.service.delete_file(g.identity, pid_value, key)
        return "", 204


request_files_view_args = request_parser(
    {"bucket_id": ma.fields.Str(required=True), "key": ma.fields.Str()},
    location="view_args",
)


class LegacyFilesRESTResourceConfig(RDMDraftFilesResourceConfig):
    """Legacy Files-REST resource config."""

    blueprint_name = "legacy_files_rest"
    url_prefix = "/files"

    response_handlers = {
        "application/json": ResponseHandler(
            LegacyFilesRESTJSONSerializer(), headers=etag_headers
        ),
    }

    routes = {
        "files-list": "/<bucket_id>",
        "files-item": "/<bucket_id>/<key>",
    }


class LegacyFilesRESTResource(FileResource):
    """Legacy Files-REST resource."""

    def create_url_rules(self):
        """Create the URL rules for the draft files resource."""
        routes = self.config.routes
        url_rules = [
            route("GET", routes["files-list"], self.search),
            route("GET", routes["files-item"], self.get_object),
            route("PUT", routes["files-item"], self.set_object),
            route("DELETE", routes["files-item"], self.delete_object),
        ]

        return url_rules

    @request_files_view_args
    @response_handler(many=True)
    def search(self):
        """List files."""
        bucket_id = resource_requestctx.view_args["bucket_id"]
        record = self.service.get_record_by_bucket_id(bucket_id)
        files = self.service.list_files(g.identity, record["id"])
        return files.to_dict(), 200

    @request_files_view_args
    @response_handler()
    def get_object(self):
        """Get file as in Files-REST views."""
        bucket_id = resource_requestctx.view_args["bucket_id"]
        key = resource_requestctx.view_args["key"]
        record = self.service.get_record_by_bucket_id(bucket_id)

        item = self.service.get_file_content(g.identity, record["id"], key)
        if item is None:
            abort(404)

        return item.send_file(), 200

    @request_stream
    @request_files_view_args
    @response_handler()
    def set_object(self):
        """Upload/set a file as in Files-REST views."""
        bucket_id = resource_requestctx.view_args["bucket_id"]
        key = resource_requestctx.view_args["key"]
        stream = resource_requestctx.data["request_stream"]
        content_length = resource_requestctx.data["request_content_length"]
        record = self.service.get_record_by_bucket_id(bucket_id)

        # TODO: Maybe move this to the service?
        with UnitOfWork() as uow:
            # If the file exists already, delete first
            try:
                item = self.service.get_file_content(g.identity, record["id"], key)
                if item:
                    self.service.delete_file(g.identity, record["id"], key, uow=uow)
            except FileKeyNotFoundError:
                pass

            self.service.init_files(g.identity, record["id"], [{"key": key}], uow=uow)
            self.service.set_file_content(
                g.identity,
                record["id"],
                key,
                stream,
                content_length=content_length,
                uow=uow,
            )
            item = self.service.commit_file(g.identity, record["id"], key, uow=uow)
            uow.commit()

        return item.to_dict(), 201

    @request_files_view_args
    @response_handler()
    def delete_object(self):
        """Delete a file as in Files-REST views."""
        bucket_id = resource_requestctx.view_args["bucket_id"]
        key = resource_requestctx.view_args["key"]
        record = self.service.get_record_by_bucket_id(bucket_id)

        item = self.service.delete_file(g.identity, record["id"], key)
        return item.to_dict(), 204
