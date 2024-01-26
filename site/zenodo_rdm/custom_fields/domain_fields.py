# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""
from invenio_i18n import lazy_gettext as _
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


BIODIV_FIELDS = [
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
    # dc
    KeywordCF(name="dc:creator", multiple=True),
    KeywordCF(name="dc:rightsHolder", multiple=True),
    # openbiodiv
    KeywordCF(name="openbiodiv:TaxonomicConceptLabel", multiple=True),
    # obo
    RelationshipListCF(name="obo:RO_0002453"),
]

AUDIOVIS_FIELDS = [
    # ac
    KeywordCF(name="ac:associatedSpecimenReference", multiple=True),
    KeywordCF(name="ac:captureDevice", multiple=True),
    KeywordCF(name="ac:physicalSetting", multiple=True),
    KeywordCF(name="ac:resourceCreationTechnique", multiple=True),
    KeywordCF(name="ac:subjectOrientation", multiple=True),
    KeywordCF(name="ac:subjectPart", multiple=True),
]

BIODIVERSITY_FIELDS_UI = {
    "section": _("Biodiversity"),
    "icon": "leaf",
    "hide_from_upload_form": False,
    "compose_fields": True,  # marks the group as dynamic
    "fields": [
        dict(
            field="dwc:basisOfRecord",
            ui_widget="MultiInput",
            props=dict(
                label=_("Basis of record"),
                type="text",
                multiple_values=True
            ),
        ),
        dict(
            field="dwc:catalogNumber",
            ui_widget="MultiInput",
            props=dict(
                label=_("Catalog number"),
            ),
        ),
        dict(
            field="dwc:class",
            ui_widget="MultiInput",
            props=dict(
                label=_("Class"),
            ),
        ),
        dict(
            field="dwc:collectionCode",
            ui_widget="MultiInput",
            props=dict(
                label=_("Collection code"),
            ),
        ),
        dict(
            field="dwc:country",
            ui_widget="MultiInput",
            props=dict(
                label=_("Country"),
            ),
        ),
        dict(
            field="dwc:county",
            ui_widget="MultiInput",
            props=dict(
                label=_("County"),
            ),
        ),
        dict(
            field="dwc:dateIdentified",
            ui_widget="MultiInput",
            props=dict(
                label=_("Date identified"),
            ),
        ),
        dict(
            field="dwc:decimalLatitude",
            ui_widget="MultiInput",
            props=dict(
                label=_("Decimal latitude"),
            ),
        ),
        dict(
            field="dwc:decimalLongitude",
            ui_widget="MultiInput",
            props=dict(
                label=_("Decimal longitude"),
            ),
        ),
        dict(
            field="dwc:eventDate",
            ui_widget="MultiInput",
            props=dict(
                label=_("Event date"),
                description=_("Insert date in YYYY-MM-DD format")
            ),
        ),
        dict(
            field="dwc:family",
            ui_widget="MultiInput",
            props=dict(
                label=_("Family"),
            ),
        ),
        dict(
            field="dwc:genus",
            ui_widget="MultiInput",
            props=dict(
                label=_("Genus"),
            ),
        ),
        dict(
            field="dwc:identifiedBy",
            ui_widget="MultiInput",
            props=dict(
                label=_("Identified by"),
            ),
        ),
        dict(
            field="dwc:individualCount",
            ui_widget="MultiInput",
            props=dict(
                label=_("Individual count"),
            ),
        ),
        dict(
            field="dwc:institutionCode",
            ui_widget="MultiInput",
            props=dict(
                label=_("Institution code"),
            ),
        ),
        dict(
            field="dwc:kingdom",
            ui_widget="MultiInput",
            props=dict(
                label=_("Kingdom"),
            ),
        ),
        dict(
            field="dwc:lifeStage",
            ui_widget="MultiInput",
            props=dict(
                label=_("Life stage"),
            ),
        ),
        dict(
            field="dwc:locality",
            ui_widget="MultiInput",
            props=dict(
                label=_("Locality"),
            ),
        ),
        dict(
            field="dwc:materialSampleID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Material sample ID"),
            ),
        ),
        dict(
            field="dwc:namePublishedInID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Name published in ID"),
            ),
        ),
        dict(
            field="dwc:namePublishedInYear",
            ui_widget="MultiInput",
            props=dict(
                label=_("Name published in year"),
            ),
        ),
        dict(
            field="dwc:order",
            ui_widget="MultiInput",
            props=dict(
                label=_("Order"),
            ),
        ),
        dict(
            field="dwc:otherCatalogNumbers",
            ui_widget="MultiInput",
            props=dict(
                label=_("Other catalogue numbers"),
            ),
        ),
        dict(
            field="dwc:phylum",
            ui_widget="MultiInput",
            props=dict(
                label=_("Phylum"),
            ),
        ),
        dict(
            field="dwc:preparations",
            ui_widget="MultiInput",
            props=dict(
                label=_("Preparations"),
            ),
        ),
        dict(
            field="dwc:recordedBy",
            ui_widget="MultiInput",
            props=dict(
                label=_("Recorded by"),
            ),
        ),
        dict(
            field="dwc:scientificName",
            ui_widget="MultiInput",
            props=dict(
                label=_("Scientific name"),
            ),
        ),
        dict(
            field="dwc:scientificNameAuthorship",
            ui_widget="MultiInput",
            props=dict(
                label=_("Scientific name authorship"),
            ),
        ),
        dict(
            field="dwc:scientificNameID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Scientific name ID"),
            ),
        ),
        dict(
            field="dwc:sex",
            ui_widget="MultiInput",
            props=dict(
                label=_("Sex"),
            ),
        ),
        dict(
            field="dwc:specificEpithet",
            ui_widget="MultiInput",
            props=dict(
                label=_("Species"),
            ),
        ),
        dict(
            field="dwc:taxonID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxon ID"),
            ),
        ),
        dict(
            field="dwc:taxonomicStatus",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxonomic status"),
            ),
        ),
        dict(
            field="dwc:taxonRank",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxon rank"),
            ),
        ),
        dict(
            field="dwc:typeStatus",
            ui_widget="MultiInput",
            props=dict(
                label=_("Type status"),
            ),
        ),
        dict(
            field="dwc:verbatimElevation",
            ui_widget="MultiInput",
            props=dict(
                label=_("Verbatim elevation"),
            ),
        ),
        dict(
            field="dwc:verbatimEventDate",
            ui_widget="MultiInput",
            props=dict(
                label=_("Verbatim event date"),
            ),
        ),
        # gbif-dwc
        dict(
            field="gbif-dwc:recordedByID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Recorded by ID"),
            ),
        ),
        dict(
            field="gbif-dwc:identifiedByID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Identified by ID"),
            ),
        ),
        # openbiodiv
        dict(
            field="openbiodiv:TaxonomicConceptLabel",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxonomic concept label"),
            ),
        ),
        dict(
            field="dc:creator",
            ui_widget="MultiInput",
            props=dict(
                label=_("Creator"),
            ),
        ),
        dict(
            field="dc:rightsHolder",
            ui_widget="MultiInput",
            props=dict(
                label=_("Rights holder"),
            ),
        ),
        # obo
        dict(
            field="obo:RO_0002453",
            template="zenodo_rdm/obo.html",
            ui_widget="MultiInput",
            props=dict(
                label="Host of",
            ),
        ),
    ],
}

AUDIOVIS_FIELDS_UI = {
    "section": _("Audiovisual core"),
    "icon": "camera",
    "hide_from_upload_form": False,
    "compose_fields": True,  # marks the group as dynamic
    "fields": [
        dict(
            field="ac:associatedSpecimenReference",
            ui_widget="MultiInput",
            props=dict(
                label=_("Associated specimen reference"),
            ),
        ),
        dict(
            field="ac:physicalSetting",
            ui_widget="MultiInput",
            props=dict(
                label=_("Physical setting"),
            ),
        ),
        dict(
            field="ac:captureDevice",
            ui_widget="MultiInput",
            props=dict(
                label=_("Capture device"),
            ),
        ),
        dict(
            field="ac:resourceCreationTechnique",
            ui_widget="MultiInput",
            props=dict(
                label=_("Resource creation technique"),
                note="""Information about technical aspects of the creation and 
                digitization process of the resource. This includes modification 
                steps (\"retouching\") after the initial resource capture."""
            ),
        ),
        dict(
            field="ac:subjectPart",
            ui_widget="MultiInput",
            props=dict(
                label=_("Subject part"),
            ),
        ),
    ],
}
