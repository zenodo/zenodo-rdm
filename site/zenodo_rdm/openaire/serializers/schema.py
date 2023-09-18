# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAire schema."""

from flask import current_app
from marshmallow import Schema, fields, missing, pre_dump
from marshmallow_utils.fields import ISODateString

from zenodo_rdm.openaire.utils import (
    get_resource_type_vocabulary,
    openaire_datasource_id,
    openaire_original_id,
)


class OpenAIRESchema(Schema):
    """Schema for records in OpenAIRE-JSON.

    OpenAIRE Schema: https://www.openaire.eu/schema/1.0/oaf-result-1.0.xsd
    OpenAIRE Vocabularies: http://api.openaire.eu/vocabularies
    """

    originalId = fields.Method("get_original_id", required=True)
    title = fields.Str(attribute="metadata.title", required=True)
    description = fields.Str(attribute="metadata.description")
    url = fields.Method("get_url", required=True)

    authors = fields.List(fields.Str(attribute="name"), attribute="metadata.creators")

    language = fields.Str(attribute="metadata.language")
    version = fields.Str(attribute="metadata.version")
    contexts = fields.Method("get_communities")

    licenseCode = fields.Method("get_license_code", required=True)
    embargoEndDate = ISODateString(attribute="metadata.embargo_date")

    publisher = fields.Method("get_publisher")
    collectedFromId = fields.Method("get_datasource_id", required=True)
    hostedById = fields.Method("get_datasource_id")

    linksToProjects = fields.Method("get_links_to_projects")
    pids = fields.Method("get_pids")

    @pre_dump
    def add_oatypes(self, data, **kwargs):
        """Add oatype once to the record.

        It is added on ``pre_dump`` since it requires the vocabulary to be read.
        """
        resource_type = data.get("metadata", {}).get("resource_type")
        if not resource_type:
            return missing

        oatype = get_resource_type_vocabulary(resource_type)

        # Oatype is a dictionary
        data["type"] = oatype["openaire_type"]
        data["resourceType"] = oatype["openaire_resourceType"]
        return data

    def get_original_id(self, obj):
        """Get Original Id."""
        # Added on pre_dump
        oatype = obj["type"]

        if oatype:
            # ID value is stored in a tuple on position 1
            return openaire_original_id(obj, oatype)[1]

        return missing

    def get_datasource_id(self, obj):
        """Get OpenAIRE datasource identifier."""
        return openaire_datasource_id(obj) or missing

    def get_communities(self, obj):
        """Get record's communities."""
        communities = []
        record_comms = obj.get("parent", {}).get("communities", [])
        base_url = current_app.config["SITE_UI_URL"]
        for comm in record_comms:
            # TODO do we get links? Otherwise, we can build it with app config SITE_URL
            communities.append(f"{base_url}/communities/{comm}")
        return communities or missing

    # Mapped from: http://api.openaire.eu/vocabularies/dnet:access_modes
    LICENSE_MAPPING = {
        "open": "OPEN",
        "embargoed": "EMBARGO",
        "restricted": "RESTRICTED",
        "closed": "CLOSED",
    }

    def get_license_code(self, obj):
        """Get license code."""
        access = obj.get("access", {})

        is_open = access["record"] == "public" and access["files"] == "public"
        is_embargo = access.get("embargo", {}).get("active")
        is_restricted = access["record"] == "public" and access["files"] == "restricted"

        key = ""

        if is_open:
            key = "open"
        elif is_restricted:
            key = "is_restricted"
        elif is_embargo:
            key = "is_embargo"

        return self.LICENSE_MAPPING.get(key, "UNKNOWN")

    def get_links_to_projects(self, obj):
        """Get project/grant links."""
        metadata = obj.get("metadata")
        grants = metadata.get("funding", [])
        links = []
        for grant in grants:
            award = grant.get("award", {})
            # TODO confirm this one
            eurepo = award.get("identifiers", {}).get("eurepo", "")
            if eurepo:
                links.append(
                    "{eurepo}/{title}/{acronym}".format(
                        eurepo=eurepo,
                        title=grant.get("title", "").replace("/", "%2F"),
                        acronym=grant.get("acronym", ""),
                    )
                )
        return links or missing

    def get_pids(self, obj):
        """Get record PIDs."""
        pids = obj.get("pids", {})
        result = []
        if "doi" in pids:
            pids.append({"type": "doi", "value": pids["doi"]["identifier"]})
        if "oai" in pids:
            pids.append({"type": "oai", "value": pids["oai"]["identifier"]})
        return result

    def get_url(self, obj):
        """Get record URL."""
        base_url = current_app.config["SITE_UI_URL"]

        recid = obj["id"]

        # TODO does the record contain links?
        return f"{base_url}/records/{recid}"

    def get_publisher(self, obj):
        """Get publisher."""
        pub = obj["metadata"].get("publisher")
        return pub or missing
