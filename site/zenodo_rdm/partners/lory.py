# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""LORY payloads and settings."""

PAYLOAD = {
    "metadata": {
        # Communities
        "communities": [
            {"identifier": "lory"},
            {"identifier": "lory_unilu"},
            {"identifier": "lory_unilu_rf"},
        ],
        #
        # Required/basic fields
        #
        # Resource type
        "upload_type": "publication",
        "publication_type": "article",
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
        "notes": "+ zhb_151741 + Reihe: Luzerner historische Ver\u00f6ffentlichungen, Bd. 7",
        # Access
        "access_right": "open",
        "license": "CC-BY-NC-ND-4.0",
        # Journal
        "journal_title": "Journal of Global Buddhism",
        "journal_volume": "1",
        "journal_issue": "12, Dec. 2011",
        "journal_pages": "31-55",
        # Conference
        "conference_title": "DHIK Forum 2022 - Angewandte Forschung und Transfer im internationalen Rahmen",
        "conference_acronym": "DHIK",
        "conference_dates": "9 June 2022",
        "conference_place": "Hochschule Luzern - Departement Technik und Architektur, Technikumstrasse 21, CH-6048 Horw",
        "conference_url": "https://www.hslu.ch/dhik-forum-22",
        "conference_session": "13",
        "conference_session_part": "1",
        # Imprint
        "imprint_publisher": "Zenodo",
        "imprint_place": "Horw",
        "imprint_isbn": "0393-2990",
        "partof_title": "Some 'part of' title",
        "partof_pages": "234",
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
        "thesis_university": "Hochschule Luzern \u2013 Soziale Arbeit",
    }
}
