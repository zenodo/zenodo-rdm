# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo-RDM service schema."""

from invenio_rdm_records.services.schemas import RDMRecordSchema
from marshmallow import Schema, fields


class SWHSchema(Schema):
    """Software Heritage schema."""

    swhid = fields.Str()


class ZenodoRecordSchema(RDMRecordSchema):
    """Zenodo service schema.

    This schema subclasses the base schema and extends it with Zenodo-specific
    fields.
    """

    swh = fields.Nested(SWHSchema, dump_only=True)
