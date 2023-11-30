# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""
from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.contrib.codemeta import (
    CODEMETA_CUSTOM_FIELDS,
    CODEMETA_CUSTOM_FIELDS_UI,
    CODEMETA_FACETS,
    CODEMETA_NAMESPACE,
)
from invenio_rdm_records.contrib.imprint import (
    IMPRINT_CUSTOM_FIELDS,
    IMPRINT_CUSTOM_FIELDS_UI,
    IMPRINT_NAMESPACE,
)
from invenio_rdm_records.contrib.journal import (
    JOURNAL_CUSTOM_FIELDS,
    JOURNAL_CUSTOM_FIELDS_UI,
    JOURNAL_NAMESPACE,
)
from invenio_rdm_records.contrib.meeting import (
    MEETING_CUSTOM_FIELDS,
    MEETING_CUSTOM_FIELDS_UI,
    MEETING_NAMESPACE,
)
from invenio_rdm_records.contrib.thesis import (
    THESIS_CUSTOM_FIELDS,
    THESIS_CUSTOM_FIELDS_UI,
    THESIS_NAMESPACE,
)
from invenio_records_resources.services.custom_fields import (
    BaseCF,
    DoubleCF,
    ISODateStringCF,
    KeywordCF,
    TextCF,
)
from marshmallow import fields
from marshmallow_utils.fields import SanitizedUnicode


class SubjectListCF(BaseCF):
    """Subject list custom field."""

    @property
    def mapping(self):
        """Search mapping."""
        return {
            "type": "object",
            "properties": {
                "term": {"type": "keyword"},
                "identifier": {"type": "keyword"},
                "scheme": {"type": "keyword"},
            },
        }

    @property
    def field(self):
        """Marshmallow field."""
        return fields.List(
            fields.Nested(
                {
                    "term": SanitizedUnicode(),
                    "identifier": SanitizedUnicode(),
                    "scheme": SanitizedUnicode(),
                }
            )
        )


LEGACY_CUSTOM_FIELDS = [
    KeywordCF(name="legacy:communities", multiple=True),
    SubjectListCF(name="legacy:subjects"),
]
"""Legacy compatibility custom fields."""


class RelationshipListCF(BaseCF):
    """Relationship list custom field."""

    @property
    def mapping(self):
        """Search mapping using nested."""
        return {
            # NOTE: "object" wouldn't work for what we're querying
            "type": "nested",
            "properties": {
                "subject": {"type": "keyword"},
                "object": {"type": "keyword"},
            },
        }

    @property
    def field(self):
        """Marshmallow field."""
        # For example see "Host of" on https://zenodo.org/record/3949282
        return fields.List(
            fields.Nested(
                {
                    "subject": fields.List(SanitizedUnicode(required=True)),
                    "object": fields.List(SanitizedUnicode(required=True)),
                }
            )
        )


NAMESPACES = {
    "dwc": "http://rs.tdwg.org/dwc/terms/",
    "gbif-dwc": "http://rs.gbif.org/terms/1.0/",
    "ac": "http://rs.tdwg.org/ac/terms/",
    "openbiodiv": "http://openbiodiv.net/ontology#",
    "obo": "http://purl.obolibrary.org/obo/",
    "dc": "http://purl.org/dc/terms/",
    "legacy": "",
    **CODEMETA_NAMESPACE,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
    **JOURNAL_NAMESPACE,
    **MEETING_NAMESPACE,
    **IMPRINT_NAMESPACE,
    **THESIS_NAMESPACE,
}

CUSTOM_FIELDS = [
    # dwc
    KeywordCF(name="dwc:basisOfRecord", multiple=True),
    KeywordCF(name="dwc:catalogNumber", multiple=True),
    KeywordCF(name="dwc:class", multiple=True),
    KeywordCF(name="dwc:collectionCode", multiple=True),
    KeywordCF(name="dwc:country", multiple=True),
    KeywordCF(name="dwc:county", multiple=True),
    ISODateStringCF(name="dwc:dateIdentified", multiple=True),
    DoubleCF(name="dwc:decimalLatitude", multiple=True),
    DoubleCF(name="dwc:decimalLongitude", multiple=True),
    ISODateStringCF(name="dwc:eventDate", multiple=True),
    KeywordCF(name="dwc:family", multiple=True),
    KeywordCF(name="dwc:genus", multiple=True),
    KeywordCF(name="dwc:identifiedBy", multiple=True),
    KeywordCF(name="dwc:individualCount", multiple=True),
    KeywordCF(name="dwc:institutionCode", multiple=True),
    KeywordCF(name="dwc:kingdom", multiple=True),
    KeywordCF(name="dwc:lifeStage", multiple=True),
    KeywordCF(name="dwc:locality", multiple=True),
    KeywordCF(name="dwc:materialSampleID", multiple=True),
    KeywordCF(name="dwc:namePublishedInID", multiple=True),
    KeywordCF(name="dwc:namePublishedInYear", multiple=True),
    KeywordCF(name="dwc:order", multiple=True),
    KeywordCF(name="dwc:otherCatalogNumbers", multiple=True),
    KeywordCF(name="dwc:phylum", multiple=True),
    KeywordCF(name="dwc:preparations", multiple=True),
    KeywordCF(name="dwc:recordedBy", multiple=True),
    KeywordCF(name="dwc:scientificName", multiple=True),
    TextCF(name="dwc:scientificNameAuthorship", multiple=True),
    KeywordCF(name="dwc:scientificNameID", multiple=True),
    KeywordCF(name="dwc:sex", multiple=True),
    KeywordCF(name="dwc:specificEpithet", multiple=True),
    KeywordCF(name="dwc:stateProvince", multiple=True),
    KeywordCF(name="dwc:taxonID", multiple=True),
    KeywordCF(name="dwc:taxonRank", multiple=True),
    KeywordCF(name="dwc:taxonomicStatus", multiple=True),
    KeywordCF(name="dwc:typeStatus", multiple=True),
    KeywordCF(name="dwc:verbatimElevation", multiple=True),
    KeywordCF(name="dwc:verbatimEventDate", multiple=True),
    # gbif-dwc
    KeywordCF(name="gbif-dwc:identifiedByID", multiple=True),
    KeywordCF(name="gbif-dwc:recordedByID", multiple=True),
    # ac
    KeywordCF(name="ac:associatedSpecimenReference", multiple=True),
    KeywordCF(name="ac:captureDevice", multiple=True),
    KeywordCF(name="ac:physicalSetting", multiple=True),
    KeywordCF(name="ac:resourceCreationTechnique", multiple=True),
    KeywordCF(name="ac:subjectOrientation", multiple=True),
    KeywordCF(name="ac:subjectPart", multiple=True),
    # dc
    KeywordCF(name="dc:creator", multiple=True),
    KeywordCF(name="dc:rightsHolder", multiple=True),
    # openbiodiv
    KeywordCF(name="openbiodiv:TaxonomicConceptLabel", multiple=True),
    # obo
    RelationshipListCF(name="obo:RO_0002453"),
    # codemeta,
    *CODEMETA_CUSTOM_FIELDS,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
    # journal
    *JOURNAL_CUSTOM_FIELDS,
    # meeting
    *MEETING_CUSTOM_FIELDS,
    # imprint
    *IMPRINT_CUSTOM_FIELDS,
    # thesis
    *THESIS_CUSTOM_FIELDS,
    # legacy
    *LEGACY_CUSTOM_FIELDS,
]

ZENODO_CUSTOM_FIELDS_UI = {
    "section": _("Biodiversity"),
    "hide_from_upload_form": True,
    "fields": [
        # dwc
        dict(
            field="dwc:basisOfRecord",
            props=dict(
                label="Basis of record",
            ),
        ),
        dict(
            field="dwc:catalogNumber",
            props=dict(
                label="Catalog number",
            ),
        ),
        dict(
            field="dwc:class",
            props=dict(
                label="Class",
            ),
        ),
        dict(
            field="dwc:collectionCode",
            props=dict(
                label="Collection code",
            ),
        ),
        dict(
            field="dwc:country",
            props=dict(
                label="Country",
            ),
        ),
        dict(
            field="dwc:county",
            props=dict(
                label="County",
            ),
        ),
        dict(
            field="dwc:dateIdentified",
            props=dict(
                label="Date identified",
            ),
        ),
        dict(
            field="dwc:decimalLatitude",
            props=dict(
                label="Decimal latitude",
            ),
        ),
        dict(
            field="dwc:decimalLongitude",
            props=dict(
                label="Decimal longitude",
            ),
        ),
        dict(
            field="dwc:eventDate",
            props=dict(
                label="Event date",
            ),
        ),
        dict(
            field="dwc:family",
            props=dict(
                label="Family",
            ),
        ),
        dict(
            field="dwc:genus",
            props=dict(
                label="Genus",
            ),
        ),
        dict(
            field="dwc:identifiedBy",
            props=dict(
                label="Identified by",
            ),
        ),
        dict(
            field="dwc:individualCount",
            props=dict(
                label="Individual count",
            ),
        ),
        dict(
            field="dwc:institutionCode",
            props=dict(
                label="Institution code",
            ),
        ),
        dict(
            field="dwc:kingdom",
            props=dict(
                label="Kingdom",
            ),
        ),
        dict(
            field="dwc:lifeStage",
            props=dict(
                label="Life stage",
            ),
        ),
        dict(
            field="dwc:locality",
            props=dict(
                label="Locality",
            ),
        ),
        dict(
            field="dwc:materialSampleID",
            props=dict(
                label="Material sample ID",
            ),
        ),
        dict(
            field="dwc:namePublishedInID",
            props=dict(
                label="Name published in ID",
            ),
        ),
        dict(
            field="dwc:namePublishedInYear",
            props=dict(
                label="Name published in year",
            ),
        ),
        dict(
            field="dwc:order",
            props=dict(
                label="Order",
            ),
        ),
        dict(
            field="dwc:class",
            props=dict(
                label="Class",
            ),
        ),
        dict(
            field="dwc:otherCatalogNumbers",
            props=dict(
                label="Other catalog numbers",
            ),
        ),
        dict(
            field="dwc:phylum",
            props=dict(
                label="Phylum",
            ),
        ),
        dict(
            field="dwc:preparations",
            props=dict(
                label="Preparations",
            ),
        ),
        dict(
            field="dwc:recordedBy",
            props=dict(
                label="Recorded by",
            ),
        ),
        dict(
            field="dwc:scientificName",
            props=dict(
                label="Scientific name",
            ),
        ),
        dict(
            field="dwc:scientificNameAuthorship",
            props=dict(
                label="Scientific name authorship",
            ),
        ),
        dict(
            field="dwc:scientificNameID",
            props=dict(
                label="Scientific name ID",
            ),
        ),
        dict(
            field="dwc:sex",
            props=dict(
                label="Sex",
            ),
        ),
        dict(
            field="dwc:specificEpithet",
            props=dict(
                label="Species",
            ),
        ),
        dict(
            field="dwc:taxonID",
            props=dict(
                label="Taxon ID",
            ),
        ),
        dict(
            field="dwc:taxonomicStatus",
            props=dict(
                label="Taxonomic status",
            ),
        ),
        dict(
            field="dwc:taxonRank",
            props=dict(
                label="Taxon rank",
            ),
        ),
        dict(
            field="dwc:typeStatus",
            props=dict(
                label="Type status",
            ),
        ),
        dict(
            field="dwc:verbatimElevation",
            props=dict(
                label="Verbatim elevation",
            ),
        ),
        dict(
            field="dwc:verbatimEventDate",
            props=dict(
                label="Verbatim event date",
            ),
        ),
        # gbif-dwc
        dict(
            field="gbif-dwc:recordedByID",
            props=dict(
                label="Recorded by ID",
            ),
        ),
        dict(
            field="gbif-dwc:identifiedByID",
            props=dict(
                label="Identified by ID",
            ),
        ),
        dict(
            field="ac:associatedSpecimenReference",
            props=dict(
                label="Associated specimen reference",
            ),
        ),
        dict(
            field="ac:physicalSetting",
            props=dict(
                label="Physical setting",
            ),
        ),
        dict(
            field="ac:associatedSpecimenReference",
            props=dict(
                label="Associated specimen reference",
            ),
        ),
        dict(
            field="ac:captureDevice",
            props=dict(
                label="Capture device",
            ),
        ),
        dict(
            field="ac:resourceCreationTechnique",
            props=dict(
                label="Resource creation technique",
            ),
        ),
        dict(
            field="ac:subjectOrientation",
            props=dict(
                label="Subject orientation",
            ),
        ),
        dict(
            field="ac:subjectPart",
            props=dict(
                label="Subject part",
            ),
        ),
        # dc
        dict(
            field="dc:creator",
            props=dict(
                label="Creator",
            ),
        ),
        dict(
            field="dc:rightsHolder",
            props=dict(
                label="Rights holder",
            ),
        ),
        # openbiodiv
        dict(
            field="openbiodiv:TaxonomicConceptLabel",
            props=dict(
                label="Taxonomic concept label",
            ),
        ),
        # obo
        dict(
            field="obo:RO_0002453",
            template="zenodo_rdm/obo.html",
            props=dict(
                label="Host of",
            ),
        ),
    ],
}

# hide meeting section from Additional details in landing page
MEETING_CUSTOM_FIELDS_UI["hide_from_landing_page"] = True

# Custom fields UI components
CUSTOM_FIELDS_UI = [
    # zenodo custom fields
    ZENODO_CUSTOM_FIELDS_UI,
    # codemeta
    CODEMETA_CUSTOM_FIELDS_UI,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
    # publishing information
    {
        "section": _("Publishing information"),
        "hide_from_landing_page": True,  # hide meeting section from Additional details in landing page
        "fields": [
            # journal
            *JOURNAL_CUSTOM_FIELDS_UI["fields"],
            # imprint
            *IMPRINT_CUSTOM_FIELDS_UI["fields"],
            # thesis
            *THESIS_CUSTOM_FIELDS_UI["fields"],
        ],
    },
    # meeting
    MEETING_CUSTOM_FIELDS_UI,
]

# Custom fields facets

CUSTOM_FIELDS_FACETS = {
    **CODEMETA_FACETS,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
}
