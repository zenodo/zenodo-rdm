# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""
from invenio_i18n import lazy_gettext as _
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
    # journal
    *JOURNAL_CUSTOM_FIELDS,
    # meeting
    *MEETING_CUSTOM_FIELDS,
    # imprint
    *IMPRINT_CUSTOM_FIELDS,
    # thesis
    *THESIS_CUSTOM_FIELDS,
]

# hide meeting section
MEETING_CUSTOM_FIELDS_UI["hidden"] = True

# Custom fields UI components
CUSTOM_FIELDS_UI = [
    {
        "section": _("Publishing information"),
        "hidden": True,
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
