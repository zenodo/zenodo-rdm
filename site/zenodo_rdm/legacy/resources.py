# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy resources."""

from functools import partial, wraps

import marshmallow as ma
from flask import abort, g, jsonify, request
from flask_resources import (
    RequestBodyParser,
    ResponseHandler,
    request_parser,
    resource_requestctx,
    response_handler,
    route,
)
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.resources.config import (
    RDMDraftFilesResourceConfig,
    RDMRecordMediaFilesResourceConfig,
    RDMRecordResourceConfig,
)
from invenio_rdm_records.resources.resources import RDMRecordResource
from invenio_records_resources.resources.files.resource import (
    FileResource,
    request_stream,
    request_view_args,
    set_max_content_length,
)
from invenio_records_resources.resources.records.headers import etag_headers
from invenio_records_resources.services.errors import (
    FailedFileUploadException,
    FileKeyNotFoundError,
)
from invenio_records_resources.services.uow import UnitOfWork
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import secure_filename

from .deserializers import LegacyJSONDeserializer
from .serializers import (
    LegacyDraftFileJSONSerializer,
    LegacyFilesRESTJSONSerializer,
    LegacyJSONSerializer,
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
            set_content_result = self.service.set_file_content(
                g.identity, pid_value, key, file, uow=uow
            )
            if set_content_result.to_dict().get("errors"):
                raise FailedFileUploadException(
                    recid=pid_value,
                    file=set_content_result.to_dict(),
                    file_key=key,
                )
            commit_file_result = self.service.commit_file(
                g.identity, pid_value, key, uow=uow
            )
            uow.commit()

        return commit_file_result.to_dict(), 201

    @request_draft_files_view_args
    @response_handler()
    def read(self):
        """Read a single file."""
        pid_value = resource_requestctx.view_args["pid_value"]
        file_id = resource_requestctx.view_args["file_id"]
        key = self.service.get_file_key_by_id(pid_value, file_id)
        if key is None:
            abort(404)
        item = self.service.get_file_content(g.identity, pid_value, key)
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


def _create_or_update_file(
    files_service,
    key,
    stream,
    content_length,
    pid_value,
    identity=None,
):
    """Create or update a draft/record file."""
    identity = identity or g.identity
    with UnitOfWork() as uow:
        # If the file exists already, delete first
        try:
            read_file_result = files_service.read_file_metadata(
                identity, pid_value, key
            )
            if read_file_result:
                files_service.delete_file(identity, pid_value, key, uow=uow)
        except FileKeyNotFoundError:
            pass

        files_service.init_files(identity, pid_value, [{"key": key}], uow=uow)
        set_content_result = files_service.set_file_content(
            identity,
            pid_value,
            key,
            stream,
            content_length=content_length,
            uow=uow,
        )
        if set_content_result.to_dict().get("errors"):
            raise FailedFileUploadException(
                recid=pid_value,
                file=set_content_result.to_dict(),
                file_key=key,
            )
        commit_file_result = files_service.commit_file(
            identity, pid_value, key, uow=uow
        )
        uow.commit()
    return commit_file_result


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

    @set_max_content_length
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

        commit_file_result = _create_or_update_file(
            self.service, key, stream, content_length, record["id"]
        )

        return commit_file_result.to_dict(), 201

    @request_files_view_args
    @response_handler()
    def delete_object(self):
        """Delete a file as in Files-REST views."""
        bucket_id = resource_requestctx.view_args["bucket_id"]
        key = resource_requestctx.view_args["key"]
        record = self.service.get_record_by_bucket_id(bucket_id)

        self.service.delete_file(g.identity, record["id"], key)
        return "", 204


def parse_extra_formats_mimetype(
    from_query_string=None,
    from_content_type=None,
    from_accept=None,
):
    """Decorator to parse the request's extra formats MIMEType."""
    assert from_content_type or from_accept or from_query_string

    mimetype = None
    if from_query_string:
        mimetype = request.args.get("mimetype")
    if not mimetype and from_content_type:
        mimetype = request.headers.get("Content-Type")
    if not mimetype and from_accept:
        mimetype = next((m for m, _ in request.accept_mimetypes), None)
    if not mimetype:
        return abort(400, "Invalid extra format MIMEType.")
    return mimetype


class DraftExtraFormatsResourceConfig(RDMDraftFilesResourceConfig):
    """Draft extra formats resource config."""

    allow_upload = True
    allow_archive_download = False
    blueprint_name = "legacy_draft_extra_formats"
    url_prefix = "/deposit/depositions"
    routes = {
        "list": "/<pid_value>/formats",
    }


class DraftExtraFormatsResource(FileResource):
    """Draft extra formats resource."""

    decorators = []  # disable content negotiation

    def create_url_rules(self):
        """Routing for the views."""
        routes = self.config.routes
        _route = partial(route, rule_options=dict(provide_automatic_options=False))
        url_rules = [
            _route("GET", routes["list"], self.get),
            _route("PUT", routes["list"], self.put),
            _route("DELETE", routes["list"], self.delete),
            _route("OPTIONS", routes["list"], self.search),
        ]
        return url_rules

    def _get_draft_or_record(self, identity, id_, action):
        try:
            # If the draft is being edited, add the file to the draft
            record = self.service.read_draft(identity, id_)._record
        except (NoResultFound, PIDDoesNotExistError):
            # Else add it to the record directly
            record = self.service.read(identity, id_)._record

        # NOTE: We check the permission here as a "draft", so that we can later use
        # ``system_identity`` for potentially deleting a file from a published record.
        self.service.draft_files.require_permission(g.identity, action, record=record)
        return record

    @request_view_args
    def get(self):
        """Get an extra format."""
        pid_value = resource_requestctx.view_args["pid_value"]
        mimetype = parse_extra_formats_mimetype(
            from_query_string=True,
            from_accept=True,
        )
        record = self._get_draft_or_record(g.identity, pid_value, "read_files")
        if record.files.enabled is False:
            abort(404)
        if record.is_draft:
            service = self.service.draft_files
        else:
            service = self.service.files
        item = service.get_file_content(g.identity, pid_value, mimetype)
        return item.send_file(), 200

    @request_view_args
    def put(self):
        """Create or replace an extra format file."""
        pid_value = resource_requestctx.view_args["pid_value"]
        key = parse_extra_formats_mimetype(from_content_type=True)
        stream = request.stream
        content_length = request.content_length
        record = self._get_draft_or_record(g.identity, pid_value, "create_files")
        if record.files.enabled is False:
            record.files.enabled = True
            record.files.create_bucket()
            record.commit()

        if record.is_draft:
            media_files_service = self.service.draft_files
        else:
            media_files_service = self.service.files

        _create_or_update_file(
            media_files_service,
            key,
            stream,
            content_length,
            pid_value,
            identity=system_identity,
        )
        return {"message": f'Extra format "{key}" updated.'}, 200

    @request_view_args
    def delete(self):
        """Delete an extra format file."""
        pid_value = resource_requestctx.view_args["pid_value"]
        key = parse_extra_formats_mimetype(from_content_type=True)

        record = self._get_draft_or_record(g.identity, pid_value, "delete_files")
        if record.is_draft:
            media_files_service = self.service.draft_files
        else:
            media_files_service = self.service.files
        media_files_service.delete_file(system_identity, pid_value, key)
        return {"message": f'Extra format "{key}" deleted.'}, 200

    @request_view_args
    def search(self):
        """Get a list of all extra formats files."""
        pid_value = resource_requestctx.view_args["pid_value"]
        record = self._get_draft_or_record(g.identity, pid_value, "read_files")
        if record.is_draft:
            files = self.service.draft_files.list_files(g.identity, pid_value)
        else:
            files = self.service.files.list_files(g.identity, pid_value)
        res = files.to_dict()
        if res.get("entries"):
            return res["entries"], 200
        return jsonify([]), 200


class RecordExtraFormatsResourceConfig(RDMRecordMediaFilesResourceConfig):
    """Record extra formats resource config."""

    allow_upload = False
    allow_archive_download = False
    blueprint_name = "legacy_record_extra_formats"
    url_prefix = "/records"
    routes = {
        "list": "/<pid_value>/formats",
    }


class RecordExtraFormatsResource(FileResource):
    """Record extra formats resource."""

    decorators = []  # disable content negotiation

    def create_url_rules(self):
        """Routing for the views."""
        routes = self.config.routes

        _route = partial(route, rule_options=dict(provide_automatic_options=False))
        url_rules = [
            _route("GET", routes["list"], self.get),
            _route("OPTIONS", routes["list"], self.search),
        ]
        return url_rules

    @request_view_args
    def get(self):
        """Get extra format file."""
        pid_value = resource_requestctx.view_args["pid_value"]
        key = parse_extra_formats_mimetype(from_query_string=True, from_accept=True)

        record = self.service.read(g.identity, pid_value)._record
        if record.files.enabled is False:
            abort(404)
        item = self.service.files.get_file_content(g.identity, pid_value, key)
        return item.send_file(), 200

    @request_view_args
    def search(self):
        """Get available extra formats files."""
        pid_value = resource_requestctx.view_args["pid_value"]
        record = self.service.read(g.identity, pid_value)._record
        if record.files.enabled is False:
            return jsonify([]), 200
        files = self.service.files.list_files(g.identity, pid_value)
        res = files.to_dict()
        if res.get("entries"):
            return res["entries"], 200
        return jsonify([]), 200
