# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test record transform for RDM migration."""

from datetime import datetime
from unittest.mock import patch

import dictdiffer
import pytest

from zenodo_rdm.migrator.errors import InvalidIdentifier
from zenodo_rdm.migrator.transform.entries.records.metadata import (
    ZenodoRecordMetadataEntry,
)
from zenodo_rdm.migrator.transform.records import (
    ZenodoDraftEntry,
    ZenodoRecordEntry,
    ZenodoRecordTransform,
)

###
# RECORD
###


@pytest.fixture(scope="function")
def zenodo_record_data():
    """Full Zenodo record as a dictionary."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "id": "2d6970ea-602d-4e8b-a918-063a59823386",
        "json": {
            "doi": "10.5281/zenodo.1234567",
            "_oai": {
                "id": "oai:zenodo.org:10452",
                "sets": ["openaire_data", "user-zenodo"],
                "updated": "2020-01-24T19:25:21Z",
            },
            "conceptrecid": "10122",
            "recid": "10123",
            "access_right": "open",
            "resource_type": {"type": "image", "subtype": "photo"},
            "publication_date": "2023-01-01",
            "title": "Migration test photo",
            "_files": [
                {
                    "key": "file_one.txt",
                    "size": 100,
                    "type": "txt",
                    "bucket": "264de9f5-d321-4427-93cc-3280ca82f148",
                    "file_id": "49fcf62d-9636-40be-b058-f51b4b2a027d",
                    "checksum": "md5:e6e3ba3ecbf1c6169c98e24dd7104fbd",
                    "version_id": "5acb6d0b-28f4-4db1-a99b-30f5d176ebaa",
                },
                {
                    "key": "file_two.txt",
                    "size": 200,
                    "type": "txt",
                    "bucket": "264de9f5-d321-4427-93cc-3280ca82f148",
                    "file_id": "290d4fdb-2295-4c39-a123-b0af093d6c89",
                    "checksum": "md5:62b15872f1239e21d2fce63fa4f4614a",
                    "version_id": "db532a75-66c7-45e7-a57f-25edfba08afc",
                },
            ],
            "owners": [1234],
            "$schema": "https://zenodo.org/schemas/records/record-v1.0.0.json",
            "license": {"$ref": "http://dx.zenodo.org/licenses/cc-zero"},
            "_buckets": {
                "record": "264de9f5-d321-4427-93cc-3280ca82f148",
                "deposit": "7868b45e-1c8d-4490-8a3d-9a759422ef9c",
            },
            "_deposit": {
                "id": "7695",
                "pid": {"type": "recid", "value": "10122"},
                "owners": [1234],
                "status": "published",
                "created_by": 1234,
            },
            "creators": [
                {
                    "gnd": "",
                    "name": "Doe, John",
                    "orcid": "0000-0001-6759-6273",
                    "familyname": "Doe",
                    "givennames": "John",
                    "affiliation": "CERN",
                }
            ],
            "contributors": [
                {
                    "name": "Else, Someone",
                    "orcid": "0000-0001-6759-6273",
                    "type": "ContactPerson",
                    "affiliation": "CERN",
                },
            ],
            "dates": [
                {
                    "start": "2018-03-21",
                    "end": "2018-03-25",
                    "type": "Collected",
                    "description": "Another collection period.",
                },
                {
                    "start": "2018-03-21",
                    "end": "2018-03-21",
                    "type": "Valid",
                    "description": "A date",
                },
                {
                    "start": "2018-03-21",
                    "type": "Withdrawn",
                    "description": "A date",
                },
                {
                    "end": "2018-03-21",
                    "type": "Collected",
                    "description": "A date",
                },
            ],
            "grants": [
                {"$ref": "https://dx.zenodo.org/grants/10.13039/501100000780::278850"}
            ],
            "locations": [
                {"lat": 34.02577, "lon": -118.7804, "place": "Los Angeles"},
                {
                    "place": "Mt.Fuji, Japan",
                    "description": "Sample found 100ft from the foot of the mountain.",
                },
            ],
            "notes": "A note",
            "license": {"$ref": "https://dx.zenodo.org/licenses/cc-zero"},
            "language": "eng",
            "alternate_identifiers": [
                {
                    "identifier": "10.13039/901100010730",
                    "resource_type": {"subtype": "thesis", "type": "publication"},
                    "scheme": "doi",
                }
            ],
            "related_identifiers": [
                {
                    "identifier": "10.13039/901100010730",
                    "relation": "isCitedBy",
                    "resource_type": {
                        "subtype": "annotationcollection",
                        "type": "publication",
                    },
                    "scheme": "doi",
                }
            ],
            "references": [{"raw_reference": "Test reference"}],
            "keywords": ["migration", "test", "Zenodo", "RDM"],
            "_internal": {
                "source": {
                    "agents": [
                        {
                            "role": "uploader",
                            "email": "john.doe@test.com",
                            "user_id": "1234",
                            "username": "jdoe",
                        }
                    ]
                }
            },
            "communities": ["zenodo", "migration"],
            "description": "This is a full Zenodo record that needs to be tested for migration",
            "journal": {
                "title": "Testing journal",
                "issue": "10",
                "pages": "35-40",
                "volume": "20",
                "issn": "2414-2948",
            },
            "meeting": {
                "url": "http://test-meeting.com/",
                "dates": "20th–30th Jan 2023",
                "place": "Geneva, Switzerland",
                "title": "Zenodo to RDM migration planning.",
                "acronym": "ZenodoRDM",
                "session": "First meeting",
                "session_part": "Afternoon session",
            },
            "imprint": {
                "isbn": "2192-6247",
                "place": "Geneva",
                "publisher": "CERN's Publishing",
            },
            "part_of": {"pages": "13-123", "title": "A book title"},
            "thesis": {
                "university": "Test University",
                "supervisors": [
                    {
                        "gnd": "",
                        "name": "Doe, Jane",
                        "orcid": "0000-0001-6759-6273",
                        "familyname": "Doe",
                        "givennames": "Jane",
                        "affiliation": "CERN",
                    }
                ],
            },
            "custom": {
                # dwc
                "dwc:basisOfRecord": ["foo", "bar"],
                "dwc:catalogNumber": ["foo", "bar"],
                "dwc:class": ["foo", "bar"],
                "dwc:collectionCode": ["MUSM", "ZMPC"],
                "dwc:country": ["foo", "bar"],
                "dwc:county": ["foo", "bar"],
                "dwc:dateIdentified": ["2011-05-17", "2022-08-18"],
                "dwc:decimalLatitude": ["foo", "bar"],
                "dwc:decimalLongitude": ["foo", "bar"],
                "dwc:eventDate": ["2011-05-17", "2022-08-18"],
                "dwc:family": ["Cerambycidae"],
                "dwc:genus": ["Asynapteron"],
                "dwc:identifiedBy": ["foo", "bar"],
                "dwc:individualCount": ["foo", "bar"],
                "dwc:institutionCode": ["foo", "bar"],
                "dwc:kingdom": ["Animalia"],
                "dwc:lifeStage": ["foo", "bar"],
                "dwc:locality": ["foo", "bar"],
                "dwc:materialSampleID": ["foo", "bar"],
                "dwc:namePublishedInID": ["foo", "bar"],
                "dwc:namePublishedInYear": ["foo", "bar"],
                "dwc:order": ["Coleoptera"],
                "dwc:otherCatalogNumbers": ["foo", "bar"],
                "dwc:phylum": ["Arthropoda"],
                "dwc:preparations": ["foo", "bar"],
                "dwc:recordedBy": ["foo", "bar"],
                "dwc:scientificName": ["foo", "bar"],
                "dwc:scientificNameAuthorship": [
                    "Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado"
                ],
                "dwc:scientificNameID": ["foo", "bar"],
                "dwc:sex": ["foo", "bar"],
                "dwc:specificEpithet": ["andinum"],
                "dwc:stateProvince": ["foo", "bar"],
                "dwc:taxonID": ["foo", "bar"],
                "dwc:taxonRank": ["species"],
                "dwc:taxonomicStatus": ["sp. nov."],
                "dwc:typeStatus": ["holotype"],
                "dwc:verbatimElevation": ["foo", "bar"],
                "dwc:verbatimEventDate": ["2011-05-17"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": [
                    "Asynapteron andinum Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado, 2023"
                ],
                # ac
                "ac:associatedSpecimenReference": ["foo", "bar"],
                "ac:captureDevice": ["foo", "bar"],
                "ac:physicalSetting": ["foo", "bar"],
                "ac:resourceCreationTechnique": ["foo", "bar"],
                "ac:subjectOrientation": ["foo", "bar"],
                "ac:subjectPart": ["foo", "bar"],
                # dc
                "dc:creator": ["foo", "bar"],
                "dc:rightsHolder": ["foo", "bar"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": ["foo", "bar"],
                # obo
                "obo:RO_0002453": [
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                ],
                # gbif-dwc
                "gbif-dwc:identifiedByID": ["foo", "bar"],
                "gbif-dwc:recordedByID": ["foo", "bar"],
            },
        },
        "version_id": 1,
    }


@pytest.fixture(scope="function")
def expected_rdm_record_entry():
    """Full Zenodo RDM record as a dictionary.

    Should contain the expected record data of processing `zenodo_record_data`.
    """
    return {
        "id": "2d6970ea-602d-4e8b-a918-063a59823386",
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "version_id": 1,
        "index": 1,
        "json": {
            "id": "10123",
            "pids": {
                "oai": {
                    "provider": "oai",
                    "identifier": "oai:zenodo.org:10452",
                },
                "doi": {
                    "client": "datacite",
                    "provider": "datacite",
                    "identifier": "10.5281/zenodo.1234567",
                },
            },
            "files": {"enabled": True},
            "metadata": {
                "title": "Migration test photo",
                "description": "This is a full Zenodo record that needs to be tested for migration",
                "publication_date": "2023-01-01",
                "resource_type": {"id": "image-photo"},
                "creators": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "identifiers": [
                                {"scheme": "orcid", "identifier": "0000-0001-6759-6273"}
                            ],
                            "name": "Doe, John",
                            "family_name": "Doe",
                            "given_name": "John",
                        },
                        "affiliations": [{"name": "CERN"}],
                    },
                ],
                "contributors": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "identifiers": [
                                {"scheme": "orcid", "identifier": "0000-0001-6759-6273"}
                            ],
                            "name": "Else, Someone",
                            "family_name": "Else",
                            "given_name": "Someone",
                        },
                        "affiliations": [{"name": "CERN"}],
                        "role": {"id": "contactperson"},
                    },
                    {
                        "person_or_org": {
                            "type": "personal",
                            "identifiers": [
                                {"scheme": "orcid", "identifier": "0000-0001-6759-6273"}
                            ],
                            "name": "Doe, Jane",
                            "family_name": "Doe",
                            "given_name": "Jane",
                        },
                        "affiliations": [{"name": "CERN"}],
                        "role": {"id": "supervisor"},
                    },
                ],
                "publisher": "CERN's Publishing",
                "rights": [{"id": "cc-by-1.0"}],
                "dates": [
                    {
                        "date": "2018-03-21/2018-03-25",
                        "type": {"id": "collected"},
                        "description": "Another collection period.",
                    },
                    {
                        "date": "2018-03-21",
                        "type": {"id": "valid"},
                        "description": "A date",
                    },
                    {
                        "date": "2018-03-21",
                        "type": {"id": "withdrawn"},
                        "description": "A date",
                    },
                    {
                        "date": "2018-03-21",
                        "type": {"id": "collected"},
                        "description": "A date",
                    },
                ],
                "funding": [
                    {
                        "award": {"id": "00k4n6c32::278850"},
                        "funder": {"id": "00k4n6c32"},
                    }
                ],
                "locations": {
                    "features": [
                        {
                            "place": "Los Angeles",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-118.7804, 34.02577],
                            },
                        },
                        {
                            "place": "Mt.Fuji, Japan",
                            "description": "Sample found 100ft from the foot of the mountain.",
                        },
                    ]
                },
                "subjects": [
                    {"subject": "migration"},
                    {"subject": "test"},
                    {"subject": "Zenodo"},
                    {"subject": "RDM"},
                ],
                "rights": [{"id": "cc0-1.0"}],
                "languages": [{"id": "eng"}],
                "identifiers": [
                    {"scheme": "doi", "identifier": "10.13039/901100010730"}
                ],
                "related_identifiers": [
                    {
                        "scheme": "doi",
                        "identifier": "10.13039/901100010730",
                        "relation_type": {"id": "iscitedby"},
                        "resource_type": {"id": "publication-annotationcollection"},
                    }
                ],
                "references": [{"reference": "Test reference"}],
                "additional_descriptions": [
                    {"description": "A note", "type": {"id": "other"}}
                ],
            },
            "access": {
                "record": "public",
                "files": "public",
            },
            "custom_fields": {
                "journal:journal": {
                    "title": "Testing journal",
                    "issue": "10",
                    "pages": "35-40",
                    "volume": "20",
                    "issn": "2414-2948",
                },
                "meeting:meeting": {
                    "url": "http://test-meeting.com/",
                    "dates": "20th–30th Jan 2023",
                    "place": "Geneva, Switzerland",
                    "title": "Zenodo to RDM migration planning.",
                    "acronym": "ZenodoRDM",
                    "session": "First meeting",
                    "session_part": "Afternoon session",
                },
                "imprint:imprint": {
                    "isbn": "2192-6247",
                    "place": "Geneva",
                    "pages": "13-123",
                    "title": "A book title",
                },
                "thesis:university": "Test University",
                # dwc
                "dwc:basisOfRecord": ["foo", "bar"],
                "dwc:catalogNumber": ["foo", "bar"],
                "dwc:class": ["foo", "bar"],
                "dwc:collectionCode": ["MUSM", "ZMPC"],
                "dwc:country": ["foo", "bar"],
                "dwc:county": ["foo", "bar"],
                "dwc:dateIdentified": ["2011-05-17", "2022-08-18"],
                "dwc:decimalLatitude": ["foo", "bar"],
                "dwc:decimalLongitude": ["foo", "bar"],
                "dwc:eventDate": ["2011-05-17", "2022-08-18"],
                "dwc:family": ["Cerambycidae"],
                "dwc:genus": ["Asynapteron"],
                "dwc:identifiedBy": ["foo", "bar"],
                "dwc:individualCount": ["foo", "bar"],
                "dwc:institutionCode": ["foo", "bar"],
                "dwc:kingdom": ["Animalia"],
                "dwc:lifeStage": ["foo", "bar"],
                "dwc:locality": ["foo", "bar"],
                "dwc:materialSampleID": ["foo", "bar"],
                "dwc:namePublishedInID": ["foo", "bar"],
                "dwc:namePublishedInYear": ["foo", "bar"],
                "dwc:order": ["Coleoptera"],
                "dwc:otherCatalogNumbers": ["foo", "bar"],
                "dwc:phylum": ["Arthropoda"],
                "dwc:preparations": ["foo", "bar"],
                "dwc:recordedBy": ["foo", "bar"],
                "dwc:scientificName": ["foo", "bar"],
                "dwc:scientificNameAuthorship": [
                    "Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado"
                ],
                "dwc:scientificNameID": ["foo", "bar"],
                "dwc:sex": ["foo", "bar"],
                "dwc:specificEpithet": ["andinum"],
                "dwc:stateProvince": ["foo", "bar"],
                "dwc:taxonID": ["foo", "bar"],
                "dwc:taxonRank": ["species"],
                "dwc:taxonomicStatus": ["sp. nov."],
                "dwc:typeStatus": ["holotype"],
                "dwc:verbatimElevation": ["foo", "bar"],
                "dwc:verbatimEventDate": ["2011-05-17"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": [
                    "Asynapteron andinum Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado, 2023"
                ],
                # ac
                "ac:associatedSpecimenReference": ["foo", "bar"],
                "ac:captureDevice": ["foo", "bar"],
                "ac:physicalSetting": ["foo", "bar"],
                "ac:resourceCreationTechnique": ["foo", "bar"],
                "ac:subjectOrientation": ["foo", "bar"],
                "ac:subjectPart": ["foo", "bar"],
                # dc
                "dc:creator": ["foo", "bar"],
                "dc:rightsHolder": ["foo", "bar"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": ["foo", "bar"],
                # obo
                "obo:RO_0002453": [
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                ],
                # gbif-dwc
                "gbif-dwc:identifiedByID": ["foo", "bar"],
                "gbif-dwc:recordedByID": ["foo", "bar"],
            },
        },
    }


@pytest.fixture(scope="function")
def expected_rdm_record_parent():
    """Full Zenodo RDM parent record as a dictionary.

    Should contain the expected parent record data of processing `zenodo_record_data`.
    """
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "version_id": 1,
        "json": {
            "id": "10122",
            "access": {"owned_by": [{"user": 1234}]},
            "communities": {"ids": ["zenodo", "migration"], "default": "zenodo"},
        },
    }


def test_record_entry(zenodo_record_data, expected_rdm_record_entry):
    """Test the transformation of a full Zenodo record."""
    result = ZenodoRecordEntry().transform(zenodo_record_data)
    assert not list(dictdiffer.diff(result, expected_rdm_record_entry))


def test_record_entry_with_restricted_files():
    """Tests the access transformation for restricted records."""
    result = ZenodoRecordEntry()._access({"json": {"access_right": "restricted"}})
    assert result == {
        "record": "public",
        "files": "restricted",
    }


def test_record_entry_with_embargoed_files():
    """Tests the access transformation for restricted records."""
    result = ZenodoRecordEntry()._access(
        {"json": {"access_right": "embargoed", "embargo_date": "2023-01-01"}}
    )
    assert result == {
        "record": "public",
        "files": "restricted",
        "embargo": {"until": "2023-01-01", "active": True},
    }


def test_record_transform_parent_record(zenodo_record_data, expected_rdm_record_parent):
    """Tests the parent record transformation."""
    result = ZenodoRecordTransform()._parent(zenodo_record_data)
    assert not list(dictdiffer.diff(result, expected_rdm_record_parent))


###
# DRAFT
###


class MockDateTime:
    """Mock datetime class."""

    def today(self):
        """ISO formatter datetime."""
        return datetime(2023, 1, 1, 12, 0, 0, 000000)


@pytest.fixture(scope="function")
def zenodo_draft_data():
    """Full Zenodo draft as a dictionary."""
    return {
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "id": "2d6970ea-602d-4e8b-a918-063a59823386",
        "json": {
            "doi": "10.5281/zenodo.1234567",
            "conceptrecid": "10122",
            "recid": "10123",
            "access_right": "open",
            "resource_type": {"type": "image", "subtype": "photo"},
            "publication_date": "2023-01-01",
            "title": "Migration test photo",
            "owners": [1234],
            "$schema": "https://zenodo.org/schemas/records/record-v1.0.0.json",
            "license": {"$ref": "http://dx.zenodo.org/licenses/cc-zero"},
            "creators": [
                {
                    "gnd": "",
                    "name": "Doe, John",
                    "orcid": "0000-0001-6759-6273",
                    "familyname": "Doe",
                    "givennames": "John",
                    "affiliation": "CERN",
                }
            ],
            "contributors": [
                {
                    "name": "Else, Someone",
                    "orcid": "0000-0001-6759-6273",
                    "type": "ContactPerson",
                    "affiliation": "CERN",
                },
            ],
            "keywords": ["migration", "test", "Zenodo", "RDM"],
            "_internal": {
                "source": {
                    "agents": [
                        {
                            "role": "uploader",
                            "email": "john.doe@test.com",
                            "user_id": "1234",
                            "username": "jdoe",
                        }
                    ]
                }
            },
            "communities": ["zenodo", "migration"],
            "description": "This is a full Zenodo record that needs to be tested for migration",
            "grants": [
                {"$ref": "https://dx.zenodo.org/grants/10.13039/501100000780::278850"}
            ],
            "journal": {
                "title": "Testing journal",
                "issue": "10",
                "pages": "35-40",
                "volume": "20",
                "issn": "2414-2948",
            },
            "locations": [
                {"lat": 34.02577, "lon": -118.7804, "place": "Los Angeles"},
                {
                    "place": "Mt.Fuji, Japan",
                    "description": "Sample found 100ft from the foot of the mountain.",
                },
            ],
            "meeting": {
                "url": "http://test-meeting.com/",
                "dates": "20th–30th Jan 2023",
                "place": "Geneva, Switzerland",
                "title": "Zenodo to RDM migration planning.",
                "acronym": "ZenodoRDM",
                "session": "First meeting",
                "session_part": "Afternoon session",
            },
            "imprint": {
                "isbn": "2192-6247",
                "place": "Geneva",
                "publisher": "CERN's Publishing",
            },
            "part_of": {"pages": "13-123", "title": "A book title"},
            "thesis": {
                "university": "Test University",
                "supervisors": [
                    {
                        "gnd": "",
                        "name": "Doe, Jane",
                        "orcid": "0000-0001-6759-6273",
                        "familyname": "Doe",
                        "givennames": "Jane",
                        "affiliation": "CERN",
                    }
                ],
            },
            "custom": {
                # dwc
                "dwc:basisOfRecord": ["foo", "bar"],
                "dwc:catalogNumber": ["foo", "bar"],
                "dwc:class": ["foo", "bar"],
                "dwc:collectionCode": ["MUSM", "ZMPC"],
                "dwc:country": ["foo", "bar"],
                "dwc:county": ["foo", "bar"],
                "dwc:dateIdentified": ["2011-05-17", "2022-08-18"],
                "dwc:decimalLatitude": ["foo", "bar"],
                "dwc:decimalLongitude": ["foo", "bar"],
                "dwc:eventDate": ["2011-05-17", "2022-08-18"],
                "dwc:family": ["Cerambycidae"],
                "dwc:genus": ["Asynapteron"],
                "dwc:identifiedBy": ["foo", "bar"],
                "dwc:individualCount": ["foo", "bar"],
                "dwc:institutionCode": ["foo", "bar"],
                "dwc:kingdom": ["Animalia"],
                "dwc:lifeStage": ["foo", "bar"],
                "dwc:locality": ["foo", "bar"],
                "dwc:materialSampleID": ["foo", "bar"],
                "dwc:namePublishedInID": ["foo", "bar"],
                "dwc:namePublishedInYear": ["foo", "bar"],
                "dwc:order": ["Coleoptera"],
                "dwc:otherCatalogNumbers": ["foo", "bar"],
                "dwc:phylum": ["Arthropoda"],
                "dwc:preparations": ["foo", "bar"],
                "dwc:recordedBy": ["foo", "bar"],
                "dwc:scientificName": ["foo", "bar"],
                "dwc:scientificNameAuthorship": [
                    "Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado"
                ],
                "dwc:scientificNameID": ["foo", "bar"],
                "dwc:sex": ["foo", "bar"],
                "dwc:specificEpithet": ["andinum"],
                "dwc:stateProvince": ["foo", "bar"],
                "dwc:taxonID": ["foo", "bar"],
                "dwc:taxonRank": ["species"],
                "dwc:taxonomicStatus": ["sp. nov."],
                "dwc:typeStatus": ["holotype"],
                "dwc:verbatimElevation": ["foo", "bar"],
                "dwc:verbatimEventDate": ["2011-05-17"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": [
                    "Asynapteron andinum Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado, 2023"
                ],
                # ac
                "ac:associatedSpecimenReference": ["foo", "bar"],
                "ac:captureDevice": ["foo", "bar"],
                "ac:physicalSetting": ["foo", "bar"],
                "ac:resourceCreationTechnique": ["foo", "bar"],
                "ac:subjectOrientation": ["foo", "bar"],
                "ac:subjectPart": ["foo", "bar"],
                # dc
                "dc:creator": ["foo", "bar"],
                "dc:rightsHolder": ["foo", "bar"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": ["foo", "bar"],
                # obo
                "obo:RO_0002453": [
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                ],
                # gbif-dwc
                "gbif-dwc:identifiedByID": ["foo", "bar"],
                "gbif-dwc:recordedByID": ["foo", "bar"],
            },
        },
        "version_id": 1,
    }


@pytest.fixture(scope="function")
def expected_rdm_draft_entry():
    """Full Zenodo RDM record as a dictionary.

    Should contain the expected record data of processing `zenodo_record_data`.
    """
    return {
        "id": "2d6970ea-602d-4e8b-a918-063a59823386",
        "created": "2023-01-01 12:00:00.00000",
        "updated": "2023-01-31 12:00:00.00000",
        "expires_at": "2024-01-01T12:00:00",
        "fork_version_id": None,
        "version_id": 1,
        "index": 1,
        "json": {
            "id": "10123",
            "pids": {},
            "files": {"enabled": True},
            "metadata": {
                "title": "Migration test photo",
                "description": "This is a full Zenodo record that needs to be tested for migration",
                "publication_date": "2023-01-01",
                "resource_type": {"id": "image-photo"},
                "creators": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "identifiers": [
                                {"scheme": "orcid", "identifier": "0000-0001-6759-6273"}
                            ],
                            "name": "Doe, John",
                            "family_name": "Doe",
                            "given_name": "John",
                        },
                        "affiliations": [{"name": "CERN"}],
                    },
                ],
                "contributors": [
                    {
                        "person_or_org": {
                            "type": "personal",
                            "identifiers": [
                                {"scheme": "orcid", "identifier": "0000-0001-6759-6273"}
                            ],
                            "name": "Else, Someone",
                            "family_name": "Else",
                            "given_name": "Someone",
                        },
                        "affiliations": [{"name": "CERN"}],
                        "role": {"id": "contactperson"},
                    },
                    {
                        "person_or_org": {
                            "type": "personal",
                            "identifiers": [
                                {"scheme": "orcid", "identifier": "0000-0001-6759-6273"}
                            ],
                            "name": "Doe, Jane",
                            "family_name": "Doe",
                            "given_name": "Jane",
                        },
                        "affiliations": [{"name": "CERN"}],
                        "role": {"id": "supervisor"},
                    },
                ],
                "funding": [
                    {
                        "award": {"id": "00k4n6c32::278850"},
                        "funder": {"id": "00k4n6c32"},
                    }
                ],
                "locations": {
                    "features": [
                        {
                            "place": "Los Angeles",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [-118.7804, 34.02577],
                            },
                        },
                        {
                            "place": "Mt.Fuji, Japan",
                            "description": "Sample found 100ft from the foot of the mountain.",
                        },
                    ]
                },
                "publisher": "CERN's Publishing",
                "rights": [{"id": "cc0-1.0"}],
                "subjects": [
                    {"subject": "migration"},
                    {"subject": "test"},
                    {"subject": "Zenodo"},
                    {"subject": "RDM"},
                ],
            },
            "access": {
                "record": "public",
                "files": "public",
            },
            "custom_fields": {
                "journal:journal": {
                    "title": "Testing journal",
                    "issue": "10",
                    "pages": "35-40",
                    "volume": "20",
                    "issn": "2414-2948",
                },
                "meeting:meeting": {
                    "url": "http://test-meeting.com/",
                    "dates": "20th–30th Jan 2023",
                    "place": "Geneva, Switzerland",
                    "title": "Zenodo to RDM migration planning.",
                    "acronym": "ZenodoRDM",
                    "session": "First meeting",
                    "session_part": "Afternoon session",
                },
                "imprint:imprint": {
                    "isbn": "2192-6247",
                    "place": "Geneva",
                    "pages": "13-123",
                    "title": "A book title",
                },
                "thesis:university": "Test University",
                # dwc
                "dwc:basisOfRecord": ["foo", "bar"],
                "dwc:catalogNumber": ["foo", "bar"],
                "dwc:class": ["foo", "bar"],
                "dwc:collectionCode": ["MUSM", "ZMPC"],
                "dwc:country": ["foo", "bar"],
                "dwc:county": ["foo", "bar"],
                "dwc:dateIdentified": ["2011-05-17", "2022-08-18"],
                "dwc:decimalLatitude": ["foo", "bar"],
                "dwc:decimalLongitude": ["foo", "bar"],
                "dwc:eventDate": ["2011-05-17", "2022-08-18"],
                "dwc:family": ["Cerambycidae"],
                "dwc:genus": ["Asynapteron"],
                "dwc:identifiedBy": ["foo", "bar"],
                "dwc:individualCount": ["foo", "bar"],
                "dwc:institutionCode": ["foo", "bar"],
                "dwc:kingdom": ["Animalia"],
                "dwc:lifeStage": ["foo", "bar"],
                "dwc:locality": ["foo", "bar"],
                "dwc:materialSampleID": ["foo", "bar"],
                "dwc:namePublishedInID": ["foo", "bar"],
                "dwc:namePublishedInYear": ["foo", "bar"],
                "dwc:order": ["Coleoptera"],
                "dwc:otherCatalogNumbers": ["foo", "bar"],
                "dwc:phylum": ["Arthropoda"],
                "dwc:preparations": ["foo", "bar"],
                "dwc:recordedBy": ["foo", "bar"],
                "dwc:scientificName": ["foo", "bar"],
                "dwc:scientificNameAuthorship": [
                    "Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado"
                ],
                "dwc:scientificNameID": ["foo", "bar"],
                "dwc:sex": ["foo", "bar"],
                "dwc:specificEpithet": ["andinum"],
                "dwc:stateProvince": ["foo", "bar"],
                "dwc:taxonID": ["foo", "bar"],
                "dwc:taxonRank": ["species"],
                "dwc:taxonomicStatus": ["sp. nov."],
                "dwc:typeStatus": ["holotype"],
                "dwc:verbatimElevation": ["foo", "bar"],
                "dwc:verbatimEventDate": ["2011-05-17"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": [
                    "Asynapteron andinum Ju\u00e1rez-No\u00e9 & Gonz\u00e1lez-Coronado, 2023"
                ],
                # ac
                "ac:associatedSpecimenReference": ["foo", "bar"],
                "ac:captureDevice": ["foo", "bar"],
                "ac:physicalSetting": ["foo", "bar"],
                "ac:resourceCreationTechnique": ["foo", "bar"],
                "ac:subjectOrientation": ["foo", "bar"],
                "ac:subjectPart": ["foo", "bar"],
                # dc
                "dc:creator": ["foo", "bar"],
                "dc:rightsHolder": ["foo", "bar"],
                # openbiodiv
                "openbiodiv:TaxonomicConceptLabel": ["foo", "bar"],
                # obo
                "obo:RO_0002453": [
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                    {"subject": ["foo", "bar"], "object": ["foo", "bar"]},
                ],
                # gbif-dwc
                "gbif-dwc:identifiedByID": ["foo", "bar"],
                "gbif-dwc:recordedByID": ["foo", "bar"],
            },
        },
    }


@patch(
    "zenodo_rdm.migrator.transform.entries.records.records.datetime",
    MockDateTime(),
)
def test_draft_entry(zenodo_draft_data, expected_rdm_draft_entry):
    """Test the transformation of a full Zenodo record."""
    result = ZenodoDraftEntry().transform(zenodo_draft_data)
    assert not list(dictdiffer.diff(result, expected_rdm_draft_entry))


@patch(
    "zenodo_rdm.migrator.transform.entries.records.records.datetime",
    MockDateTime(),
)
def test_legacy_draft_entry(zenodo_draft_data, expected_rdm_draft_entry):
    """Test the transformation of a full Zenodo record."""
    zenodo_draft_data["_deposit"] = {
        "id": "7695",
        "pid": {"type": "recid", "value": "111111"},
        "owners": [1234],
        "status": "published",
        "created_by": 1234,
    }
    result = ZenodoDraftEntry().transform(zenodo_draft_data)
    expected_rdm_draft_entry["json"]["id"] = "111111"

    assert not list(dictdiffer.diff(result, expected_rdm_draft_entry))


def test_draft_entry_no_access(zenodo_draft_data):
    """Test the transformation of a full Zenodo record."""
    zenodo_draft_data["json"].pop("access_right")
    access = ZenodoDraftEntry().transform(zenodo_draft_data)["json"]["access"]

    assert not list(
        dictdiffer.diff(
            access,
            {
                "record": "public",
                "files": "restricted",
            },
        )
    )


###
# FIELDS
###


def test_valid_identifiers():
    metadata_entry = ZenodoRecordMetadataEntry()
    valid = [
        {"identifier": "978-65-997142-0-7"},  # minimal
        {"relation": "isIdenticalTo", "identifier": "tel-00011634"},  # with extra info
        # full
        {
            "scheme": "ads",
            "relation": "isIdenticalTo",
            "identifier": "2004PhDT........43B",
        },
        # with format in the identifier
        {
            "scheme": "arxiv",
            "relation": "isSupplementTo",
            "identifier": "arXiv:1601.08082",
        },
    ]

    for identifier in valid:
        metadata_entry._validate_identifier(identifier)
        assert "scheme" in identifier.keys()
        assert identifier["scheme"]  # not empty


def test_invalid_identifiers():
    metadata_entry = ZenodoRecordMetadataEntry()
    invalid = [
        {"identifier": "local:"},  # incomplete
        {"relation": "isSupplementTo", "identifier": "hello"},  # text
        {"relation": "isSupplementTo", "identifier": "ISSN"},  # scheme as value
        {"relation": "isSupplementTo", "identifier": "arXiv:1601_.08082"},  # malformed
        {"identifier": "10.21105.joss.00018"},  # unknown
    ]

    for identifier in invalid:
        with pytest.raises(InvalidIdentifier):
            metadata_entry._validate_identifier(identifier)
