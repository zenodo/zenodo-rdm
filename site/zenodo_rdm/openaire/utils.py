# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Invenio-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAire related helpers."""

import hashlib
import urllib

import requests
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_vocabularies.proxies import current_service as vocab_service

OPENAIRE_NAMESPACE_PREFIXES = {
    "publication": "od______2659",
    "dataset": "od______2659",
    "software": "od______2659",
    "other": "od______2659",
}

OPENAIRE_ZENODO_IDS = {
    "publication": "opendoar____::2659",
    "dataset": "opendoar____::2659",
    "software": "opendoar____::2659",
    "other": "opendoar____::2659",
}

OA_PUBLICATION = "publication"
OA_DATASET = "dataset"
OA_SOFTWARE = "software"
OA_OTHER = "other"


def get_resource_type_vocabulary(resource_type):
    """Returns the matching openaire type for the given resource type."""
    vocab = vocab_service.read(
        system_identity, ("resourcetypes", resource_type), expand=True
    ).to_dict()
    return vocab


def openaire_type(record):
    """Get the OpenAIRE type of a record."""
    metadata = record.get("metadata", {})
    resource_type = metadata.get("resource_type", {}).get("id")
    rt = get_resource_type_vocabulary(resource_type)
    if not rt:
        return None

    oatype = rt["props"]["openaire_type"]

    if is_openaire_publication(record, oatype):
        return OA_PUBLICATION
    elif oatype == OA_DATASET:
        return OA_DATASET
    elif oatype == OA_SOFTWARE:
        return OA_SOFTWARE
    elif oatype == OA_OTHER:
        return OA_OTHER

    return None


def is_openaire_publication(record, oatype):
    """Determine if record is a publication for OpenAIRE.

    Is is a publication if, apart from the being a publication, one of the following criteria is met:

    - Resource has any funding
    - Resource is fully open (record and files)
    - Resource is belongs to community "ecfunded"

    """
    if not oatype or oatype != OA_PUBLICATION:
        return False

    rights = record["access"]

    # Has grants, is part of ecfunded community or is open access.
    has_grants = record.get("metadata", {}).get("funding")
    is_ecfunded = "ecfunded" in record.get("parent", {}).get("communities", {}).get(
        "ids", []
    )
    is_open = rights["record"] == "public" and rights["files"] == "public"
    if has_grants or is_ecfunded or is_open:
        return True

    return False


def openaire_original_id(record):
    """Original original identifier."""
    oatype = openaire_type(record)
    prefix = OPENAIRE_NAMESPACE_PREFIXES.get(oatype)

    value = None
    pids = record.get("pids", {})
    if oatype == OA_PUBLICATION or oatype == OA_SOFTWARE or oatype == OA_OTHER:
        value = pids.get("oai", {}).get("identifier")
    elif oatype == "dataset":
        value = pids.get("doi", {}).get("identifier")

    return prefix, value


def openaire_datasource_id(record):
    """Get OpenAIRE datasource identifier."""
    return OPENAIRE_ZENODO_IDS.get(openaire_type(record))


def openaire_request_factory(headers=None, auth=None):
    """Request factory for OpenAIRE API."""
    ses = requests.Session()
    ses.headers.update(
        headers or {"Content-type": "application/json", "Accept": "application/json"}
    )
    if not auth:
        username = current_app.config.get("OPENAIRE_API_USERNAME")
        password = current_app.config.get("OPENAIRE_API_PASSWORD")
        if username and password:
            auth = (username, password)
    ses.auth = auth
    return ses


def openaire_id(record):
    """Compute the OpenAIRE identifier."""
    prefix, identifier = openaire_original_id(record)
    if not identifier or not prefix:
        return None

    m = hashlib.md5()
    m.update(identifier.encode("utf8"))

    return "{}::{}".format(prefix, m.hexdigest())


def openaire_link(record):
    """Compute an OpenAIRE link."""
    oatype = openaire_type(record)
    doi = record.get("pids", {}).get("doi", {}).get("identifier")

    openaire_url = current_app.config["OPENAIRE_PORTAL_URL"]

    if oatype and doi:
        return f"{openaire_url}/search/{oatype}?pid={urllib.parse.quote(str(doi))}"
    return None
