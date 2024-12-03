# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo dcat serializer."""


import idutils
from datacite import schema43
from invenio_rdm_records.resources.serializers.dcat import DCATSerializer
from lxml import etree


class ZenodoDCATSerializer(DCATSerializer):
    """Zenodo DCAT Serializer."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(**options)

    def add_missing_creator_link(self, rdf_tree):
        """Add `rdf:about` attributes to <rdf:Description> within <dct:creator> if missing."""
        namespaces = rdf_tree.nsmap
        creators = rdf_tree.xpath(
            "//dct:creator/rdf:Description[not(@rdf:about)]", namespaces=namespaces
        )

        for description in creators:
            identifier_elem = description.find("dct:identifier", namespaces)
            if identifier_elem is not None:
                identifier = identifier_elem.text.strip()
                schemes = idutils.detect_identifier_schemes(identifier)
                rdf_about_url = next(
                    (
                        idutils.to_url(identifier, scheme=scheme)
                        for scheme in schemes
                        if idutils.to_url(identifier, scheme)
                    ),
                    None,
                )
                if rdf_about_url:
                    description.set(
                        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about",
                        rdf_about_url,
                    )
        return rdf_tree

    def transform_with_xslt(self, dc_record, **kwargs):
        """Transform record with XSLT and add rdf:about."""
        # Transform with base class functionality
        dc_etree = schema43.dump_etree(dc_record)
        dc_namespace = schema43.ns[None]
        dc_etree.tag = "{{{0}}}resource".format(dc_namespace)
        dcat_etree = self.xslt_transform_func(dc_etree).getroot()

        # Add the identifier links for creators if missing
        dcat_etree = self.add_missing_creator_link(dcat_etree)

        # Inject files in results (since the XSLT can't do that by default)
        files_data = dc_record.get("_files", [])
        if files_data:
            self._add_files(
                root=dcat_etree,
                files=files_data,
            )

        return dcat_etree
