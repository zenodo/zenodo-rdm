# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Implements the schemas for the support form of ZenodoRDM."""

from flask import current_app
from marshmallow import RAISE, Schema, ValidationError, fields, validate, validates
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
    """Represents support form schema."""

    class Meta:
        """Meta class."""

        unknown = RAISE

    name = fields.String(required=True)
    email = fields.String(required=True, validate=validate.Email())
    description = SanitizedHTML(required=True)
    subject = fields.String(required=True)
    category = fields.String(required=True)
    sysInfo = fields.Boolean()
    files = fields.List(fields.Raw(type="file"))

    @validates("description")
    def validate_description(self, data, **kwargs):
        """Validates if a description is within the character limits."""
        if len(data) < min_length_config:
            raise ValidationError(
                "Description length must be bigger than {} characters".format(
                    min_length_config
                )
            )
        if len(data) > max_length_config:
            raise ValidationError(
                "Description length must be smaller than {} characters".format(
                    max_length_config
                )
            )

    @validates("category")
    def validate_category(self, data, **kwargs):
        """Validates if a category is allowed."""
        if data not in self.allowed_categories:
            raise ValidationError("{} is not a valid support category".format(data))

    @cached_property
    def allowed_categories(self):
        """Allowed categories property."""
        return [c.get("key") for c in loaded_categories]
