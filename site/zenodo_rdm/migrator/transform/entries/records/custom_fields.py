# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator custom fields entry transformer."""

from invenio_rdm_migrator.transform import Entry


class ZenodoCustomFieldsEntry(Entry):
    """Custom fields entry transform."""

    @classmethod
    def _journal(cls, journal):
        """Parse journal fields."""
        return {
            "title": journal.get("title"),
            "issue": journal.get("issue"),
            "pages": journal.get("pages"),
            "volume": journal.get("volume"),
            "issn": journal.get("issn"),
        }

    @classmethod
    def _meeting(cls, meeting):
        """Parse meeting fields."""
        return {
            "acronym": meeting.get("acronym"),
            "dates": meeting.get("dates"),
            "place": meeting.get("place"),
            "session_part": meeting.get("session_part"),
            "session": meeting.get("session"),
            "title": meeting.get("title"),
            "url": meeting.get("url"),
        }

    @classmethod
    def _imprint(cls, imprint, part_of):
        """Parse imprint fields."""
        return {
            "isbn": imprint.get("isbn"),
            "place": imprint.get("place"),
            "title": part_of.get("title"),
            "pages": part_of.get("pages"),
        }

    @classmethod
    def _dwc(cls, custom):
        """Parses dwc fields."""
        return {
            "dwc:basisOfRecord": custom.get("dwc:basisOfRecord"),
            "dwc:catalogNumber": custom.get("dwc:catalogNumber"),
            "dwc:class": custom.get("dwc:class"),
            "dwc:collectionCode": custom.get("dwc:collectionCode"),
            "dwc:country": custom.get("dwc:country"),
            "dwc:county": custom.get("dwc:county"),
            "dwc:dateIdentified": custom.get("dwc:dateIdentified"),
            "dwc:decimalLatitude": custom.get("dwc:decimalLatitude"),
            "dwc:decimalLongitude": custom.get("dwc:decimalLongitude"),
            "dwc:eventDate": custom.get("dwc:eventDate"),
            "dwc:family": custom.get("dwc:family"),
            "dwc:genus": custom.get("dwc:genus"),
            "dwc:identifiedBy": custom.get("dwc:identifiedBy"),
            "dwc:individualCount": custom.get("dwc:individualCount"),
            "dwc:institutionCode": custom.get("dwc:institutionCode"),
            "dwc:kingdom": custom.get("dwc:kingdom"),
            "dwc:lifeStage": custom.get("dwc:lifeStage"),
            "dwc:locality": custom.get("dwc:locality"),
            "dwc:materialSampleID": custom.get("dwc:materialSampleID"),
            "dwc:namePublishedInID": custom.get("dwc:namePublishedInID"),
            "dwc:namePublishedInYear": custom.get("dwc:namePublishedInYear"),
            "dwc:order": custom.get("dwc:order"),
            "dwc:otherCatalogNumbers": custom.get("dwc:otherCatalogNumbers"),
            "dwc:phylum": custom.get("dwc:phylum"),
            "dwc:preparations": custom.get("dwc:preparations"),
            "dwc:recordedBy": custom.get("dwc:recordedBy"),
            "dwc:scientificName": custom.get("dwc:scientificName"),
            "dwc:scientificNameAuthorship": custom.get("dwc:scientificNameAuthorship"),
            "dwc:scientificNameID": custom.get("dwc:scientificNameID"),
            "dwc:sex": custom.get("dwc:sex"),
            "dwc:specificEpithet": custom.get("dwc:specificEpithet"),
            "dwc:stateProvince": custom.get("dwc:stateProvince"),
            "dwc:taxonID": custom.get("dwc:taxonID"),
            "dwc:taxonRank": custom.get("dwc:taxonRank"),
            "dwc:taxonomicStatus": custom.get("dwc:taxonomicStatus"),
            "dwc:typeStatus": custom.get("dwc:typeStatus"),
            "dwc:verbatimElevation": custom.get("dwc:verbatimElevation"),
            "dwc:verbatimEventDate": custom.get("dwc:verbatimEventDate"),
        }

    @classmethod
    def _gbif_dwc(cls, custom):
        """Parses gbif-dwc fields."""
        return {
            "gbif-dwc:identifiedByID": custom.get("gbif-dwc:identifiedByID"),
            "gbif-dwc:recordedByID": custom.get("gbif-dwc:recordedByID"),
        }

    @classmethod
    def _dc(cls, custom):
        """Parses dc fields."""
        return {
            "dc:creator": custom.get("dc:creator"),
            "dc:rightsHolder": custom.get("dc:rightsHolder"),
        }

    @classmethod
    def _ac(cls, custom):
        """Parses ac fields."""
        return {
            "ac:associatedSpecimenReference": custom.get(
                "ac:associatedSpecimenReference"
            ),
            "ac:captureDevice": custom.get("ac:captureDevice"),
            "ac:physicalSetting": custom.get("ac:physicalSetting"),
            "ac:resourceCreationTechnique": custom.get("ac:resourceCreationTechnique"),
            "ac:subjectOrientation": custom.get("ac:subjectOrientation"),
            "ac:subjectPart": custom.get("ac:subjectPart"),
        }

    @classmethod
    def _drop_nones(cls, d):
        """Recursively drop Nones in dict d and return a new dictionary."""
        dd = {}
        for k, v in d.items():
            if isinstance(v, dict) and v:  # second clause removes empty dicts
                dd[k] = cls._drop_nones(v)
            elif v is not None:
                dd[k] = v
        return dd

    @classmethod
    def transform(cls, entry):
        """Transform entry."""
        custom_fields = {
            "journal:journal": cls._journal(entry.get("journal", {})),
            "meeting:meeting": cls._meeting(entry.get("meeting", {})),
            "imprint:imprint": cls._imprint(
                entry.get("imprint", {}), entry.get("part_of", {})
            ),
            "thesis:university": entry.get("thesis", {}).get("university"),
            "openbiodiv:TaxonomicConceptLabel": entry.get("custom", {}).get(
                "openbiodiv:TaxonomicConceptLabel"
            ),
            "obo:RO_0002453": entry.get("custom", {}).get("obo:RO_0002453"),
            **cls._dwc(entry.get("custom", {})),
            **cls._dc(entry.get("custom", {})),
            **cls._ac(entry.get("custom", {})),
            **cls._gbif_dwc(entry.get("custom", {})),
        }

        return cls._drop_nones(custom_fields)
