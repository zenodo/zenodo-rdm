# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Subcommunities schema implementation."""

from invenio_communities.communities.schema import AffiliationRelationSchema
from invenio_communities.subcommunities.services.schema import (
    MinimalCommunitySchema as BaseMinimalSchema,
)
from invenio_communities.subcommunities.services.schema import (
    SubcommunityRequestSchema,
)
from invenio_i18n import gettext as _
from marshmallow import Schema, ValidationError, fields, post_load, validates
from marshmallow_utils.context import context_schema
from marshmallow_utils.fields import URL, SanitizedUnicode


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


class ZenodoMinimalCommunitySchema(BaseMinimalSchema):
    """Extended minimal schema for Zenodo."""

    description = SanitizedUnicode(allow_none=True)
    website = URL(allow_none=True)
    organizations = fields.List(fields.Nested(AffiliationRelationSchema))

    @post_load
    def load_default(self, data, **kwargs):
        """Override to include extra metadata fields."""
        res = super().load_default(data, **kwargs)

        extra_metadata = {
            "description": data.get("description"),
            "website": data.get("website"),
            "organizations": data.get("organizations"),
        }

        # Filter out None or empty values
        cleaned_extras = {k: v for k, v in extra_metadata.items() if v}

        res["metadata"].update(cleaned_extras)
        return res

class ZenodoSubcommunityRequestSchema(SubcommunityRequestSchema):
    """Schema for Zenodo subcommunity requests."""
    
    community = fields.Nested(ZenodoMinimalCommunitySchema)
    payload = fields.Nested(SubCommunityRequestPayloadShema)