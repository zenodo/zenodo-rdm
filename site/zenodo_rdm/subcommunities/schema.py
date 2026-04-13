# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Subcommunities schema implementation."""

from invenio_communities.subcommunities.services.schema import SubcommunityRequestSchema
from invenio_i18n import gettext as _
from marshmallow import Schema, ValidationError, fields, validates
from marshmallow_utils.context import context_schema


class SubCommunityRequestPayloadShema(Schema):
    """Schema for the payload of a subcommunity request."""

    project_id = fields.String()

    @validates("project_id")
    def validate_project_id(self, project_id):
        """Validate the project field.

        For the 'eu' community, it is a required field.
        """
        parent_community = context_schema.get().get("community")
        is_ec_community = parent_community and parent_community.slug == "eu"
        if is_ec_community and not project_id:
            raise ValidationError(_("Project is required for EC communities."))
        if project_id:
            p_str = project_id.split("::", 1)
            if len(p_str) != 2:
                raise ValidationError(
                    _(
                        "Invalid project format. Funder can't be retrieved from the project."
                    )
                )


class ZenodoSubcommunityRequestSchema(SubcommunityRequestSchema):
    """Schema for Zenodo subcommunity requests.

    Extends the SubcommunityRequestSchema with a project field.
    """

    payload = fields.Nested(SubCommunityRequestPayloadShema)
