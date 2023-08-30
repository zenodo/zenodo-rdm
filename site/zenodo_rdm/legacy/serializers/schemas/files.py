# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy files schemas."""

from marshmallow import Schema, fields
from marshmallow_utils.fields import SanitizedUnicode


class LegacyFileSchema(Schema):
    """Legacy file schema."""

    id = SanitizedUnicode(attribute="file_id")
    filename = SanitizedUnicode(attribute="key")
    filesize = fields.Number(attribute="size")
    checksum = fields.Function(lambda v: v["checksum"].split(":", 1)[1])
    links = fields.Method("dump_links", dump_only=True)

    def dump_links(self, obj):
        """Dump links with the prefix `draft_files.``."""
        return {
            k.split("draft_files.")[1]: v
            for k, v in obj["links"].items()
            if k.startswith("draft_files.")
        }


class LegacyFilesRESTSchema(Schema):
    """Legacy Files-REST schema."""

    created = SanitizedUnicode()
    updated = SanitizedUnicode()

    version_id = SanitizedUnicode()
    key = SanitizedUnicode()
    size = fields.Number()
    mimetype = SanitizedUnicode()
    checksum = SanitizedUnicode()

    is_head = fields.Constant(True)
    delete_marker = fields.Constant(False)

    links = fields.Method("dump_links", dump_only=True)

    def dump_links(self, obj):
        """Dump links with the prefix `files_rest.``."""
        return {
            k.split("files_rest.")[1]: v
            for k, v in obj["links"].items()
            if k.startswith("files_rest.")
        }
