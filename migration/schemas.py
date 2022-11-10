from marshmallow import Schema, fields, INCLUDE
from invenio_rdm_records.services.schemas import RDMRecordSchema, RDMParentSchema
from datetime import datetime, timezone
from marshmallow_utils.fields import Links, TZDateTime


class RDMRecord(RDMRecordSchema):

    pids = fields.Dict()


class ParentSchema(Schema):

    created = TZDateTime(timezone=timezone.utc, format="iso")
    updated = TZDateTime(timezone=timezone.utc, format="iso")
    version_id = fields.Int(required=True)
    id = (fields.Str(required=True),)
    json = fields.Nested(RDMParentSchema)


class RecordSchema(Schema):

    created = TZDateTime(timezone=timezone.utc, format="iso")
    updated = TZDateTime(timezone=timezone.utc, format="iso")
    version_id = fields.Int(required=True)
    index = fields.Int(required=True)
    json = fields.Nested(RDMRecord)


class DataSchema(Schema):
    class Meta:
        unknown = INCLUDE

    record = fields.Nested(RecordSchema)
    # draft = fields.Dict()
    parent = fields.Nested(ParentSchema)
    # record_files = fields.Dict()
    # TODO: we should actually have:
    # "draft_files": ...


class RecordStreamSchema(Schema):
    stream = (fields.Str(required=True),)
    id = (fields.Str(required=True),)  # unique stream id used for check a stream status
    data = fields.Nested(DataSchema, required=True)
