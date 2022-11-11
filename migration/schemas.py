from marshmallow import Schema, fields, INCLUDE, validate
from invenio_rdm_records.services.schemas import (
    RDMRecordSchema,
    RDMParentSchema,
    FilesSchema,
    AccessSchema,
)
from invenio_rdm_records.services.schemas.metadata import (
    CreatorSchema,
    PersonOrOrganizationSchema,
)
from datetime import datetime, timezone
from marshmallow_utils.fields import (
    EDTFDateString,
    SanitizedUnicode,
    SanitizedHTML,
    TZDateTime,
)
from invenio_vocabularies.services.schema import (
    VocabularyRelationSchema as VocabularySchema,
)


class PersonOrOrg(PersonOrOrganizationSchema):
    # TODO proper validate -> requires app_context
    identifiers = fields.Dict()


class Creator(CreatorSchema):
    person_or_org = fields.Nested(PersonOrOrg, required=True)


class MetadataSchema(Schema):

    resource_type = fields.Nested(VocabularySchema, required=True)
    creators = fields.List(
        fields.Nested(Creator),
        required=True,
        validate=validate.Length(min=1, error="Missing data for required field."),
    )
    title = SanitizedUnicode(required=True, validate=validate.Length(min=3))
    description = SanitizedHTML(validate=validate.Length(min=3))
    publication_date = EDTFDateString(required=True)


class RDMRecord(Schema):

    id = fields.Int(required=True)
    # TODO proper validate -> requires app_context
    pids = fields.Dict()
    files = fields.Nested(FilesSchema)
    metadata = fields.Nested(MetadataSchema)
    access = fields.Nested(AccessSchema)


class RecordSchema(Schema):

    created = TZDateTime(timezone=timezone.utc, format="iso")
    updated = TZDateTime(timezone=timezone.utc, format="iso")
    version_id = fields.Int(required=True)
    index = fields.Int(required=True)
    json = fields.Nested(RDMRecord)


class ParentSchema(Schema):

    created = TZDateTime(timezone=timezone.utc, format="iso")
    updated = TZDateTime(timezone=timezone.utc, format="iso")
    version_id = fields.Int(required=True)
    id = (fields.Str(required=True),)
    json = fields.Nested(RDMParentSchema)


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
