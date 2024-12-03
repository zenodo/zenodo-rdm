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

    def add_subjects_uri(self, rdf_tree, subjects):
        """Add valueURI of subjects to the corresponding dct:subject elements in the RDF tree."""
        namespaces = rdf_tree.nsmap
        for subject in subjects:
            value_uri = subject.get("valueURI")
            subject_label = subject.get("subject")
            subject_scheme = subject.get("subjectScheme")
            subject_props = subject.get("subjectProps", {})

            if value_uri and subject_label and subject_scheme:
                # Find the corresponding dct:subject element by prefLabel and subjectScheme
                subject_element = rdf_tree.xpath(
                    f"""
                    //dct:subject[
                        skos:Concept[
                            skos:prefLabel[text()='{subject_label}']
                            and skos:inScheme/skos:ConceptScheme/dct:title[text()='{subject_scheme}']
                        ]
                    ]
                    """,
                    namespaces=namespaces,
                )[0]

                if subject_element:
                    # Add the valueURI to the dct:subject element as rdf:about
                    subject_element.set(
                        "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about", value_uri
                    )

                # Check if
                #  subject has a definition in its props
                definition = subject_props.get("definition")
                if definition:
                    concept_elem = subject_element.find(
                        ".//skos:Concept", namespaces=namespaces
                    )
                    if concept_elem is not None:
                        skos_definition = etree.Element(
                            "{http://www.w3.org/2004/02/skos/core#}definition"
                        )
                        skos_definition.text = definition
                        concept_elem.append(skos_definition)

        return rdf_tree

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

        # Add valueURI to subjects
        subjects = dc_record.get("subjects", [])
        if subjects:
            dcat_etree = self.add_subjects_uri(dcat_etree, subjects)

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
