# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAire schema."""

from invenio_access.permissions import system_identity
from invenio_communities.proxies import current_communities
from marshmallow import Schema, fields, missing, pre_dump
from zenodo_legacy.funders import FUNDER_ACRONYMS, FUNDER_ROR_TO_DOI

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

    authors = fields.Method("get_authors")

    language = fields.Method("get_language")
    version = fields.Str(attribute="metadata.version")
    contexts = fields.Method("get_communities")

    licenseCode = fields.Method("get_license_code", required=True)

    embargoEndDate = fields.Method("get_embargo_date")

    publisher = fields.Method("get_publisher")
    collectedFromId = fields.Method("get_datasource_id", required=True)
    hostedById = fields.Method("get_datasource_id")

    linksToProjects = fields.Method("get_links_to_projects")
    pids = fields.Method("get_pids")

    type = fields.Method("get_type")
    resourceType = fields.Method("get_resource_type")

    @pre_dump
    def add_oatypes(self, data, **kwargs):
        """Add oatype once to the record.

        It is added on ``pre_dump`` since it requires the vocabulary to be read.
        """
        resource_type = data.get("metadata", {}).get("resource_type", {}).get("id")
        if not resource_type:
            return missing

        oatype = get_resource_type_vocabulary(resource_type)

        # Oatype is a dictionary
        data["type"] = oatype["props"]["openaire_type"]
        data["resourceType"] = oatype["props"]["openaire_resourceType"]
        return data

    def get_type(self, obj):
        """Get OpenAIRE type."""
        # Added in ``pre_dump``
        return obj["type"]

    def get_resource_type(self, obj):
        """Get OpenAIRE resourceType."""
        # Added in ``pre_dump``
        return obj["resourceType"]

    def get_authors(self, obj):
        """Get authors."""
        creators = obj.get("metadata", {}).get("creators", [])
        if not creators:
            return missing

        result = []
        for c in creators:
            if c["person_or_org"]["type"] == "personal":
                result.append(c["person_or_org"]["name"])
        return result

    def get_original_id(self, obj):
        """Get Original Id."""
        # Added on pre_dump
        oatype = obj["type"]

        if oatype:
            # ID value is stored in a tuple on position 1
            return openaire_original_id(obj)[1]

        return missing

    def get_datasource_id(self, obj):
        """Get OpenAIRE datasource identifier."""
        return openaire_datasource_id(obj) or missing

    def get_communities(self, obj):
        """Get record's communities."""
        result = []
        comm_service = current_communities.service
        community_ids = obj.get("parent", {}).get("communities", {}).get("ids", [])
        communities = comm_service.read_many(system_identity, community_ids)
        for comm in communities:
            result.append(comm["links"]["self_html"])
        return result or missing

    # Mapped from: http://api.openaire.eu/vocabularies/dnet:access_modes
    LICENSE_MAPPING = {
        "open": "OPEN",
        "embargoed": "EMBARGO",
        "restricted": "RESTRICTED",
        "closed": "CLOSED",
    }

    def get_license_code(self, obj):
        """Get license code.

        .. note::

            The license code depends on the record's access. It is mapped as follows:

            Record | Files | AllowReqs   |   Access

               O       O        -              O
               O       R        T              R
               O       R        F              C
               R       O        -              -
               R       R        T              R
               R       R        F              C

            Caption:

                O : Open
                R : Restricted
                C : Closed
                - : irrelevant
                T : True
                F : False

        """
        access = obj.get("access", {})

        is_embargo = access.get("embargo", {}).get("active")
        public_record = access["record"] == "public"
        public_files = access["files"] == "public"

        access_settings = obj.get("parent").get("access").get("settings")
        allow_user_requests = access_settings.get("allow_user_requests")
        allow_guest_requests = access_settings.get("allow_guest_requests")
        allows_any = allow_user_requests or allow_guest_requests

        is_open = public_record and public_files
        is_restricted = not is_open and allows_any
        is_closed = not is_open and not allows_any

        key = ""

        if is_embargo:
            key = "embargoed"
        elif is_open:
            key = "open"
        elif is_restricted:
            key = "restricted"
        elif is_closed:
            key = "closed"

        return self.LICENSE_MAPPING.get(key, "UNKNOWN")

    def get_links_to_projects(self, obj):
        """Get project/grant links."""

        def _reverse_funder_acronym(funder_ror):
            """Retrieves funder acronym from funder's ror."""
            funder_doi = FUNDER_ROR_TO_DOI.get(funder_ror, "")
            funder_acronym = FUNDER_ACRONYMS.get(funder_doi, "")
            return funder_acronym

        metadata = obj.get("metadata")
        grants = metadata.get("funding", [])
        links = []
        for grant in grants:
            award = grant.get("award", {})
            funder = grant.get("funder", {})
            if funder and award:
                funder_ror = funder.get("id")
                funder_acronym = _reverse_funder_acronym(funder_ror)
                award_program = award.get("program", "")
                award_number = award.get("number", "")
                if funder_acronym and award_program and award_number:
                    links.append(
                        f"info:eu-repo/grantAgreement/{funder_acronym}/{award_program}/{award_number}"
                    )
        return links or missing

    def get_pids(self, obj):
        """Get record PIDs."""
        pids = obj.get("pids", {})
        result = []
        if "doi" in pids:
            result.append({"type": "doi", "value": pids["doi"]["identifier"]})
        if "oai" in pids:
            result.append({"type": "oai", "value": pids["oai"]["identifier"]})
        return result

    def get_url(self, obj):
        """Get record URL."""
        return obj["links"]["self_html"]

    def get_publisher(self, obj):
        """Get publisher."""
        pub = obj["metadata"].get("publisher")
        return pub or missing

    def get_embargo_date(self, obj):
        """Returns record's embargo date, if any."""
        access = obj.get("access", {})
        embargo_obj = access.get("embargo", {})
        is_embargo = embargo_obj.get("active")

        if not is_embargo:
            return missing

        embargo_date = embargo_obj["until"]
        return embargo_date

    def get_language(self, obj):
        """Get language.

        In RDM, there can be multiple languages. Therefore, we serialize only the first one.
        """
        langs = obj["metadata"].get("languages", [])
        if langs:
            return langs[0]["id"]
        return missing
