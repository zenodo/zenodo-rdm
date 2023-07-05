# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Base payloads and utilities."""

import io
import secrets
from datetime import datetime, timedelta


def rand_bytes_file(name, size=10):
    """Generate an in-memory file pointer with random hex string content."""
    fp = io.BytesIO(secrets.token_hex(size).encode("utf-8"))
    fp.name = name
    return fp


FULL_METADATA = {
    "metadata": {
        # Communities
        # "communities": [{"identifier": "c1"}],
        #
        # Required/basic fields
        #
        # Resource type
        "upload_type": "dataset",
        # "upload_type": "publication",
        # "publication_type": "book",
        # "upload_type": "image",
        # "image_type": "figure",
        "publication_date": "2013-09-12",
        "title": "Test title",
        "description": "Some description",
        "creators": [
            {
                "name": "Doe, John",
                "affiliation": "Atlantis",
                "orcid": "0000-0002-1825-0097",
                "gnd": "170118215",
            },
            {
                "name": "Smith, Jane",
                "affiliation": "Atlantis",
            },
        ],
        # External DOI
        # "doi": "10.1234/foo.bar",
        # "prereserve_doi": True,
        "version": "v1.0.0",
        "language": "fre",
        "keywords": ["Keyword 1", "keyword 2"],
        "notes": "Some notes",
        # Access
        "access_right": "open",
        # "access_right": "closed",
        # "access_right": "embargoed",
        # "embargo_date": (datetime.utcnow().date() + timedelta(days=1)).isoformat(),
        # "access_right": "restricted",
        # "access_conditions": "You have to be affiliated with XYZ to request access.",
        "license": "cc-zero",
        # Funding
        "grants": [
            {"id": "10.13039/501100001665::755021"},
        ],
        # Related/alternate identifiers
        "related_identifiers": [
            {
                "identifier": "10.1234/foo.bar2",
                "relation": "isCitedBy",
                "scheme": "doi",
            },
            {
                "identifier": "10.1234/foo.bar3",
                "relation": "cites",
                "scheme": "doi",
                "resource_type": "dataset",
            },
            # TODO commented since scheme ads not supported in rdm
            # {
            #     "identifier": "2011ApJS..192...18K",
            #     "relation": "isAlternateIdentifier",
            #     "scheme": "ads",
            #     "resource_type": "publication-article",
            # },
        ],
        # Contributors
        "contributors": [
            {
                "name": "Doe, Jochen",
                "affiliation": "Atlantis",
                "type": "Other",
            },
            {
                "name": "Smith, Marco",
                "affiliation": "Atlantis",
                "orcid": "0000-0002-1825-0097",
                "gnd": "170118215",
                "type": "DataCurator",
            },
        ],
        # References
        "references": [
            "Reference 1",
            "Reference 2",
        ],
        # Journal
        "journal_title": "Some journal name",
        "journal_volume": "Some volume",
        "journal_issue": "Some issue",
        "journal_pages": "Some pages",
        # Conference
        "conference_title": "Some title",
        "conference_acronym": "Some acronym",
        "conference_dates": "Some dates",
        "conference_place": "Some place",
        "conference_url": "http://someurl.com",
        "conference_session": "VI",
        "conference_session_part": "1",
        # Imprint
        "imprint_publisher": "Zenodo",
        "imprint_place": "Some place",
        "imprint_isbn": "978-3-16-148410-0",
        "partof_title": "Some part of title",
        "partof_pages": "SOme part of",
        # Thesis
        "thesis_supervisors": [
            {"name": "Doe, John", "affiliation": "Atlantis"},
            {
                "name": "Smith, Jane",
                "affiliation": "Atlantis",
                "orcid": "0000-0002-1825-0097",
                "gnd": "170118215",
            },
        ],
        "thesis_university": "Some thesis_university",
        # Subjects
        "subjects": [
            {"scheme": "gnd", "identifier": "gnd:1234567899", "term": "Astronaut"},
            {"scheme": "gnd", "identifier": "gnd:1234567898", "term": "Amish"},
        ],
        # Locations
        "locations": [
            {
                "place": "London",
                "description": "A nice location",
                "lat": 10.2,
                "lon": 5,
            },
            {
                "place": "Lisbon",
                "lat": 5.1231221,
                "lon": 1.23232323,
            },
        ],
        # Dates
        "dates": [
            {
                "start": "2018-03-21",
                "end": "2018-03-25",
                "type": "Collected",
                "description": "Specimen A5 collection period.",
            },
        ],
        # Custom
        # "custom": {
        #     "dwc:genus": "Felis",
        # },
        # Misc
        "method": "This is the method used to collect this data.",
    }
}
