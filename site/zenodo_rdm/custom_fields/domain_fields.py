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
    "discoverable_fields": True,  # marks the section with discoverable fields
    "fields": [
        dict(
            field="dwc:basisOfRecord",
            ui_widget="MultiInput",
            props=dict(
                label=_("Basis of record"),
                type="text",
                multiple_values=True,
                note=_(
                    "The specific nature of the data record, e.g., PreservedSpecimen, Observation."
                ),
            ),
        ),
        dict(
            field="dwc:catalogNumber",
            ui_widget="MultiInput",
            props=dict(
                label=_("Catalog number"),
                note=_(
                    "An identifier for the record within the catalog or collection."
                ),
            ),
        ),
        dict(
            field="dwc:class",
            ui_widget="MultiInput",
            props=dict(
                label=_("Class"), note=_("The taxonomic class of the organism.")
            ),
        ),
        dict(
            field="dwc:collectionCode",
            ui_widget="MultiInput",
            props=dict(
                label=_("Collection code"),
                note=_(
                    "A unique identifier assigned to the collection from which the record was obtained."
                ),
            ),
        ),
        dict(
            field="dwc:country",
            ui_widget="MultiInput",
            props=dict(
                label=_("Country"),
                note=_(
                    "The name of the country or major administrative unit where the specimen was collected."
                ),
            ),
        ),
        dict(
            field="dwc:county",
            ui_widget="MultiInput",
            props=dict(
                label=_("County"),
                note=_(
                    "The name of the county, shire, or equivalent where the specimen was collected."
                ),
            ),
        ),
        dict(
            field="dwc:dateIdentified",
            ui_widget="MultiInput",
            props=dict(
                label=_("Date identified"),
                note=_(
                    "The date when the specimen was identified or determined to a taxon."
                ),
            ),
        ),
        dict(
            field="dwc:decimalLatitude",
            ui_widget="MultiInput",
            props=dict(
                label=_("Decimal latitude"),
                note=_("The geographic latitude in decimal degrees."),
            ),
        ),
        dict(
            field="dwc:decimalLongitude",
            ui_widget="MultiInput",
            props=dict(
                label=_("Decimal longitude"),
                note=_("The geographic longitude in decimal degrees."),
            ),
        ),
        dict(
            field="dwc:eventDate",
            ui_widget="MultiInput",
            props=dict(
                label=_("Event date"),
                description=_("Insert date in YYYY-MM-DD format."),
                note=_(
                    "The date on which the event (e.g., collection, observation) occurred. Insert date in YYYY-MM-DD format."
                ),
            ),
        ),
        dict(
            field="dwc:family",
            ui_widget="MultiInput",
            props=dict(
                label=_("Family"),
                note=_("The name of the family to which the taxon belongs."),
            ),
        ),
        dict(
            field="dwc:genus",
            ui_widget="MultiInput",
            props=dict(
                label=_("Genus"),
                note=_("The name of the genus to which the taxon belongs."),
            ),
        ),
        dict(
            field="dwc:identifiedBy",
            ui_widget="MultiInput",
            props=dict(
                label=_("Identified by"),
                note=_("The person who identified the specimen or taxon."),
            ),
        ),
        dict(
            field="dwc:individualCount",
            ui_widget="MultiInput",
            props=dict(
                label=_("Individual count"),
                note=_("The number of individuals represented in the occurrence."),
            ),
        ),
        dict(
            field="dwc:institutionCode",
            ui_widget="MultiInput",
            props=dict(
                label=_("Institution code"),
                note=_(
                    "The code assigned to the institution where the specimen is housed."
                ),
            ),
        ),
        dict(
            field="dwc:kingdom",
            ui_widget="MultiInput",
            props=dict(
                label=_("Kingdom"), note=_("The taxonomic kingdom of the organism.")
            ),
        ),
        dict(
            field="dwc:lifeStage",
            ui_widget="MultiInput",
            props=dict(
                label=_("Life stage"),
                note=_(
                    "The developmental stage or life history status of the organism, such as 'Adult' or 'Juvenile'."
                ),
            ),
        ),
        dict(
            field="dwc:locality",
            ui_widget="MultiInput",
            props=dict(
                label=_("Locality"),
                note=_(
                    "The specific place or named location where the specimen was collected."
                ),
            ),
        ),
        dict(
            field="dwc:materialSampleID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Material sample ID"),
                note=_(
                    "An identifier for the material sample from which the occurrence was derived."
                ),
            ),
        ),
        dict(
            field="dwc:namePublishedInID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Name published in ID"),
                note=_(
                    "An identifier for the publication in which the scientific name is published."
                ),
            ),
        ),
        dict(
            field="dwc:namePublishedInYear",
            ui_widget="MultiInput",
            props=dict(
                label=_("Name published in year"),
                note=_("The year the scientific name was published."),
            ),
        ),
        dict(
            field="dwc:order",
            ui_widget="MultiInput",
            props=dict(
                label=_("Order"), note=_("The taxonomic order of the organism.")
            ),
        ),
        dict(
            field="dwc:otherCatalogNumbers",
            ui_widget="MultiInput",
            props=dict(
                label=_("Other catalogue numbers"),
                note=_(
                    "Other identifiers or catalog numbers associated with the specimen."
                ),
            ),
        ),
        dict(
            field="dwc:phylum",
            ui_widget="MultiInput",
            props=dict(
                label=_("Phylum"), note=_("The taxonomic phylum of the organism.")
            ),
        ),
        dict(
            field="dwc:preparations",
            ui_widget="MultiInput",
            props=dict(
                label=_("Preparations"),
                note=_("The physical state or type of preparation of the specimen."),
            ),
        ),
        dict(
            field="dwc:recordedBy",
            ui_widget="MultiInput",
            props=dict(
                label=_("Recorded by"),
                note=_("The person or party responsible for recording the occurrence."),
            ),
        ),
        dict(
            field="dwc:scientificName",
            ui_widget="MultiInput",
            props=dict(
                label=_("Scientific name"),
                note=_("The full scientific name, with genus and specific epithet."),
            ),
        ),
        dict(
            field="dwc:scientificNameAuthorship",
            ui_widget="MultiInput",
            props=dict(
                label=_("Scientific name authorship"),
                note=_("The authorship information for the scientific name."),
            ),
        ),
        dict(
            field="dwc:scientificNameID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Scientific name ID"),
                note=_("An identifier for the scientific name."),
            ),
        ),
        dict(
            field="dwc:sex",
            ui_widget="MultiInput",
            props=dict(label=_("Sex"), note=_("The gender or sex of the organism.")),
        ),
        dict(
            field="dwc:specificEpithet",
            ui_widget="MultiInput",
            props=dict(
                label=_("Species"),
                note=_("The species epithet in the scientific name."),
            ),
        ),
        dict(
            field="dwc:taxonID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxon ID"),
                note=_("An identifier for the taxonomic concept, often a numeric key."),
            ),
        ),
        dict(
            field="dwc:taxonomicStatus",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxonomic status"),
                note=_(
                    "The taxonomic status of the organism, e.g., 'accepted' or 'synonymized'."
                ),
            ),
        ),
        dict(
            field="dwc:taxonRank",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxon rank"),
                note=_(
                    "The taxonomic rank of the organism, e.g., 'species' or 'subspecies'."
                ),
            ),
        ),
        dict(
            field="dwc:typeStatus",
            ui_widget="MultiInput",
            props=dict(
                label=_("Type status"),
                note=_(
                    "The status of the specimen in relation to a type designation, e.g., 'holotype' or 'paratype'."
                ),
            ),
        ),
        dict(
            field="dwc:verbatimElevation",
            ui_widget="MultiInput",
            props=dict(
                label=_("Verbatim elevation"),
                note=_(
                    "The original description of the elevation as provided in the source material."
                ),
            ),
        ),
        dict(
            field="dwc:verbatimEventDate",
            ui_widget="MultiInput",
            props=dict(
                label=_("Verbatim event date"),
                note=_(
                    "The original description of the date of the event as provided in the source material."
                ),
            ),
        ),
        # gbif-dwc
        dict(
            field="gbif-dwc:recordedByID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Recorded by ID"),
                note=_(
                    "An identifier for the person who recorded the occurrence, sourced from GBIF."
                ),
            ),
        ),
        dict(
            field="gbif-dwc:identifiedByID",
            ui_widget="MultiInput",
            props=dict(
                label=_("Identified by ID"),
                note=_(
                    "An identifier for the person who identified the occurrence, sourced from GBIF."
                ),
            ),
        ),
        # openbiodiv
        dict(
            field="openbiodiv:TaxonomicConceptLabel",
            ui_widget="MultiInput",
            props=dict(
                label=_("Taxonomic concept label"),
                note=_(
                    "A human-readable label for the taxonomic concept, sourced from OpenBiodiv."
                ),
            ),
        ),
        dict(
            field="dc:creator",
            ui_widget="MultiInput",
            props=dict(
                label=_("Creator"),
                note=_(
                    "The person or organization responsible for creating the record, sourced from Dublin Core."
                ),
            ),
        ),
        dict(
            field="dc:rightsHolder",
            ui_widget="MultiInput",
            props=dict(
                label=_("Rights holder"),
                note=_(
                    "The person or organization holding rights over the record, sourced from Dublin Core."
                ),
            ),
        ),
        # TODO - needs dedicated UI widget
        # obo
        # dict(
        #     field="obo:RO_0002453",
        #     template="zenodo_rdm/obo.html",
        #     ui_widget="MultiInput",
        #     props=dict(
        #         label="Host of",
        #     ),
        # ),
    ],
}

AUDIOVIS_FIELDS_UI = {
    "section": _("Audiovisual core"),
    "icon": "camera",
    "hide_from_upload_form": False,
    "discoverable_fields": True,  # marks the section with discoverable fields
    "fields": [
        dict(
            field="ac:associatedSpecimenReference",
            ui_widget="MultiInput",
            props=dict(
                label=_("Associated specimen reference"),
                note=_("A reference to the associated specimen, if applicable."),
            ),
        ),
        dict(
            field="ac:physicalSetting",
            ui_widget="MultiInput",
            props=dict(
                label=_("Physical setting"),
                note=_(
                    "The physical environment or setting in which the resource was created or observed."
                ),
            ),
        ),
        dict(
            field="ac:captureDevice",
            ui_widget="MultiInput",
            props=dict(
                label=_("Capture device"),
                note=_(
                    "The device or equipment used to capture or create the resource."
                ),
            ),
        ),
        dict(
            field="ac:resourceCreationTechnique",
            ui_widget="MultiInput",
            props=dict(
                label=_("Resource creation technique"),
                note="""Information about technical aspects of the creation and 
                digitization process of the resource. This includes modification 
                steps (\"retouching\") after the initial resource capture.""",
            ),
        ),
        dict(
            field="ac:subjectPart",
            ui_widget="MultiInput",
            props=dict(
                label=_("Subject part"),
                note=_(
                    "The specific part or region of the subject that is the primary focus of the resource."
                ),
            ),
        ),
    ],
}
