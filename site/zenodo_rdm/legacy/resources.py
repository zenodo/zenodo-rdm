# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy resources."""

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
from invenio_i18n import gettext as _
from invenio_rdm_records.resources.config import (
    RDMDraftFilesResourceConfig,
    RDMRecordResourceConfig,
)
from invenio_rdm_records.resources.resources import RDMRecordResource
from invenio_records_resources.resources.files.resource import (
    FileResource,
    request_stream,
    request_view_args,
)
from invenio_records_resources.services.errors import FileKeyNotFoundError
from invenio_records_resources.services.uow import UnitOfWork

from .deserializers import LegacyJSONDeserializer
from .serializers import LegacyJSONSerializer


class LegacyRecordResourceConfig(RDMRecordResourceConfig):
    """Legacy record resource config."""

    blueprint_name = "legacy_records"
    url_prefix = "/deposit/depositions"

    request_body_parsers = {
        "application/json": RequestBodyParser(LegacyJSONDeserializer()),
    }

    response_handlers = {
        "application/json": ResponseHandler(LegacyJSONSerializer()),
    }

    routes = {
        "list": "",
        "item-draft": "/<pid_value>",
        "item-publish": "/<pid_value>/actions/publish",
        "item-edit": "/<pid_value>/actions/edit",
        "item-discard": "/<pid_value>/actions/discard",
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
            # route("POST", p(routes["item-discard"]), self.delete_draft),
        ]
        return url_rules


class LegacyDraftFilesResourceConfig(RDMDraftFilesResourceConfig):
    """Legacy draft files resource config."""

    blueprint_name = "legacy_draft_files"
    url_prefix = ""

    routes = {
        "list": "/deposit/depositions/<pid_value>/files",
        "item": "/deposit/depositions/<pid_value>/files/<key>",
        "files-list": "/files/<bucket_id>",
        "files-item": "/files/<bucket_id>/<key>",
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


request_files_view_args = request_parser(
    {"bucket_id": ma.fields.Str(required=True), "key": ma.fields.Str()},
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
            # TODO: Review usage
            # TODO: Used to rename a file
            # route("PUT", routes["item"], self.rename),
            # TODO: Used to sort the list of files
            # route("PUT", routes["list"], self.sort),
            # New-style API
            # TODO: Used to list files
            # route("GET", routes["files-list"], self.list_objects),
            route("GET", routes["files-item"], self.get_object),
            route("PUT", routes["files-item"], self.set_object),
            route("DELETE", routes["files-item"], self.delete_object),
        ]

        return url_rules

    @request_view_args
    @request_files_body
    @response_handler()
    def create(self):
        """Upload a file using multipart/form-data."""
        pid_value = resource_requestctx.view_args["pid_value"]
        key = resource_requestctx.data["request_data"]["name"]
        file = resource_requestctx.data["request_files"]["file"]

        # TODO: Maybe move this to the service?
        with UnitOfWork() as uow:
            self.service.init_files(g.identity, pid_value, [{"key": key}], uow=uow)
            self.service.set_file_content(g.identity, pid_value, key, file, uow=uow)
            item = self.service.commit_file(g.identity, pid_value, key, uow=uow)
            uow.commit()

        return item.to_dict(), 201

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
