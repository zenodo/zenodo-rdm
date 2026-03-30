# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
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
