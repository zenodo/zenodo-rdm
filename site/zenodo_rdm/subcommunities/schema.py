# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Subcommunities schema implementation."""

from invenio_communities.subcommunities.services.schema import (
    MinimalCommunitySchema,
    SubcommunityRequestSchema,
)
from invenio_i18n import gettext as _
from marshmallow import ValidationError, fields, post_load


class ZenodoCommunitySchema(MinimalCommunitySchema):
    """Zenodo community schema.

    Includes a project field.
    """

    project = fields.String()

    @post_load(pass_original=True)
    def process_project(self, data, original, **kwargs):
        """Validate the project field.

        For 'eu' community, it is a required field.
        """
        project = original.get("project")
        is_ec_community = self.context.get("community_slug") == "eu"
        if is_ec_community and not project:
            raise ValidationError(_("Project is required for EC communities."))
        if project:
            p_str = project.split("::", 1)
            if len(p_str) != 2:
                raise ValidationError(
                    _(
                        "Invalid project format. Funder can't be retrieved from the project."
                    )
                )
            # Funder is required and is the first part of the project identifier
            funder = p_str[0]
            data["metadata"]["funding"] = [
                {
                    "award": {"id": project},
                    "funder": {"id": funder},
                }
            ]
        return data


class ZenodoSubcommunityRequestSchema(SubcommunityRequestSchema):
    """Schema for Zenodo subcommunity requests.

    Extends the SubcommunityRequestSchema with a project field.
    """

    community = fields.Nested(ZenodoCommunitySchema)
