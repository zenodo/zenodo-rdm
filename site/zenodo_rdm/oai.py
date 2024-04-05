# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo-RDM OAI Functionality."""

from flask import g
from invenio_rdm_records.proxies import current_rdm_records_service
from lxml import etree

from .legacy.serializers import MARCXMLSerializer


def marcxml_etree(pid, record):
    """OAI MARCXML format for OAI-PMH."""
    item = current_rdm_records_service.oai_result_item(g.identity, record["_source"])
    # TODO: MARCXMLSerializer should directly be able to dump an etree instead
    # of internally creating an etree, then dump to xml, then parse into an
    # etree. See https://github.com/inveniosoftware/flask-resources/issues/117
    return etree.fromstring(
        MARCXMLSerializer().serialize_object(item.to_dict()).encode(encoding="utf-8")
    )


# Alias methods, to be deprecated
oai_marcxml_etree = marcxml_etree
