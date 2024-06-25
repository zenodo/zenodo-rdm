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
from marshmallow import fields


class ZenodoCommunitySchema(MinimalCommunitySchema):
    """Zenodo community schema.

    Includes a project field.
    """

    project = fields.String(required=True)


class ZenodoSubcommunityRequestSchema(SubcommunityRequestSchema):
    """Schema for Zenodo subcommunity requests.

    Extends the SubcommunityRequestSchema with a project field.
    """

    community = fields.Nested(ZenodoCommunitySchema)
