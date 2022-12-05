from flask import current_app
from marshmallow import (RAISE, Schema, ValidationError, fields, validate,
                         validates)
from marshmallow_utils.fields import SanitizedHTML
from werkzeug.local import LocalProxy
from werkzeug.utils import cached_property

max_length_config = LocalProxy(
    lambda: current_app.config["SUPPORT_DESCRIPTION_MAX_LENGTH"]
)

min_length_config = LocalProxy(
    lambda: current_app.config["SUPPORT_DESCRIPTION_MIN_LENGTH"]
)

loaded_categories = LocalProxy(lambda: current_app.config["SUPPORT_ISSUE_CATEGORIES"])


class SupportFormSchema(Schema):
    """Represents support form schema"""

    class Meta:
        unknown = RAISE

    name = fields.String(required=True)
    email = fields.String(required=True, validate=validate.Email())
    description = SanitizedHTML(required=True)
    subject = fields.String(required=True)
    category = fields.String(required=True)
    sysInfo = fields.Boolean()
    files = fields.List(fields.Raw(type="file"))
    recaptcha = fields.Boolean()

    @validates("description")
    def validate_description(self, data, **kwargs):
        if len(data) < min_length_config:
            raise ValidationError(
                "Description length must be longer than {} characters".format(
                    min_length_config
                )
            )
        if len(data) > max_length_config:
            raise ValidationError(
                "Description length must be shorter than {} characters".format(
                    max_length_config
                )
            )

    @validates("category")
    def validate_category(self, data, **kwargs):
        if data not in self.allowed_categories:
            raise ValidationError("{} is not a valid support category".format(data))

    @validates("recaptcha")
    def validate_recaptcha(self, data, **kwards):
        if data == False:
            raise ValidationError("Recaptcha not completed")

    @cached_property
    def allowed_categories(self):
        return [c.get("key") for c in loaded_categories]
