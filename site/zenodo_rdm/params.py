# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo search params."""

from functools import partial

from flask import request
from flask_login import current_user
from invenio_rdm_records.resources.config import RDMSearchRequestArgsSchema
from invenio_rdm_records.services.config import RDMSearchOptions
from invenio_records_resources.services.records.params.base import ParamInterpreter
from marshmallow import ValidationError, fields, pre_load, validates


class LegacyAllVersionsParam(ParamInterpreter):
    """Evaluates the 'all_versions' parameter."""

    def __init__(self, field_name, config):
        """Construct."""
        self.field_name = field_name
        super().__init__(config)

    @classmethod
    def factory(cls, field):
        """Create a new filter parameter."""
        return partial(cls, field)

    def apply(self, identity, search, params):
        """Evaluate the allversions parameter on the search."""
        all_versions = params.get("all_versions")
        if all_versions is not None:
            params["allversions"] = all_versions
        return search


class LegacyCommunitiesParam(ParamInterpreter):
    """Evaluates the 'communities' parameter."""

    def apply(self, identity, search, params):
        """Evaluate the allversions parameter on the search."""
        from invenio_communities.communities.records.api import Community

        community_slug_names = params.get("communities", [])
        community_ids = []
        for slug in community_slug_names:
            try:
                community = Community.pid.resolve(slug)  # Ensure community's existence
                community_ids.append(community.id)
            except Exception:
                # we show only results from communities that resolve
                pass

        if community_ids:
            search = search.filter("terms", **{"parent.communities.ids": community_ids})
        return search


class LegacyTypeSubtypeParam(ParamInterpreter):
    """Evaluates the 'type' and 'subtype' parameters."""

    def apply(self, identity, search, params):
        """Evaluate the allversions parameter on the search."""
        type = params.get("type")
        subtype = params.get("subtype")

        if type:
            search = search.filter(
                "term", **{"metadata.resource_type.props.type": type}
            )
            if subtype:
                subtype_id = f"{type}-{subtype}"
                search = search.filter(
                    "term", **{"metadata.resource_type.props.subtype": subtype_id}
                )
        return search


class ZenodoSearchOptions(RDMSearchOptions):
    """Zenodo search options class.

    We override to add legacy search parameters.
    """

    params_interpreters_cls = RDMSearchOptions.params_interpreters_cls + [
        LegacyCommunitiesParam,
        LegacyTypeSubtypeParam,
    ]


class ZenodoArgsSchema(RDMSearchRequestArgsSchema):
    """Zenodo search schema."""

    all_versions = fields.Boolean()
    communities = fields.List(fields.String())
    status = fields.String()
    type = fields.String()
    subtype = fields.String()

    MAX_PAGE_SIZE_AUTHENTICATED = 100
    MAX_PAGE_SIZE_GUEST = 25

    @validates("size")
    def validate_max_page_size(self, value):
        """Validate maximum page size based on user authentication."""
        if request and current_user.is_authenticated:
            if value > self.MAX_PAGE_SIZE_AUTHENTICATED:
                raise ValidationError(
                    f"Page size cannot be greater than {self.MAX_PAGE_SIZE_AUTHENTICATED}."
                )
        else:
            if value > self.MAX_PAGE_SIZE_GUEST:
                raise ValidationError(
                    f"Page size cannot be greater than {self.MAX_PAGE_SIZE_GUEST}. "
                    f"Please use authenticated requests to increase the limit to {self.MAX_PAGE_SIZE_AUTHENTICATED}."
                )

    @pre_load
    def load_all_versions(self, data, **kwargs):
        """Load legacy `all_versions` param and feed the new `allversions` one."""
        if "all_versions" in data:
            if not data["all_versions"]:
                # allow ?all_versions without explicit value
                data["allversions"] = True
            else:
                data["allversions"] = data["all_versions"]
            data.pop("all_versions", None)
        return data
