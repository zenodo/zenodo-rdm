from marshmallow import Schema, fields


class DataSchema(Schema):

    record = fields.Dict()
    draft = fields.Dict()
    parent = (fields.Dict(),)
    record_files = fields.Dict()
    # TODO: we should actually have:
    # "draft_files": ...


class RecordStreamSchema(Schema):
    stream = (fields.Str(required=True),)
    id = (fields.Str(required=True),)  # unique stream id used for check a stream status
    data = fields.Nested(DataSchema, required=True)
