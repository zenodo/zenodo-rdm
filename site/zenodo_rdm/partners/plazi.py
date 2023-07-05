# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Plazi payloads and settings."""

from datetime import datetime, timedelta

PAYLOAD = {
    "metadata": {
        # Communities
        "communities": [{"identifier": "dryad"}],
        #
        # Required/basic fields
        #
        # Resource type
        "upload_type": "dataset",
        # "upload_type": "software",
        # "upload_type": "other",
        "publication_date": "2013-09-12",
        "title": "Agrisius japonicus dubatolovi Orhant, 2012  Orhant, 2012",
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
        "keywords": ["Keyword 1", "keyword 2"],
        "notes": "Some notes",
        # Access
        "access_right": "open",
        # "access_right": "embargoed",
        # "embargo_date": (datetime.utcnow().date() + timedelta(days=1)).isoformat(),
        "license": "CC0-1.0",
        # "license": "CC-BY-4.0",
        # "license": "MIT",
        # "license": "LGPL-3.0-or-later",
        # Related/alternate identifiers
        "related_identifiers": [
            {
                "relation": "isPartOf",
                "identifier": "https://doi.org/10.11646/zootaxa.4459.1.5",
            },
            {
                "relation": "cites",
                "identifier": "https://zenodo.org/record/1458418/files/figure.png",
            },
            {
                "relation": "cites",
                "identifier": "https://zenodo.org/record/1458424/files/figure.png",
            },
        ],
        # Contributors
        "contributors": [
            {"name": "K. Ueda & Dubatolov", "type": "DataCollector"},
            {"name": "Wang Min & Dubatolov & Coll.", "type": "DataCollector"},
            {"name": "Coll.", "type": "DataCollector"},
        ],
        # Journal
        "journal_title": "On the taxonomy of the genus Agrisius Walker, 1855, with descriptions of two new species from Vietnam and Laos (Lepidoptera, Erebidae, Arctiinae)  Zootaxa",
        "journal_year": "2018",
        "journal_volume": "4459",
        "journal_issue": "1",
        "references": [
            "Orhant, G. (2012) Deux nOuVeaux Agrisius Orientaux (LepidOptera, Arctiidae, LithOsiinae). Bulletin de la Societe entomologique de Mulhouse, 68 (3), 37 - 38.",
            "Leech, J. H. (1889) 3. On the LepidOptera OF Japan and COrea. - Part II. HeterOcera, sect. I. Proceedings of the general meetings for scientific business of the Zoological Society of London, 1888, 580 - 654.",
            "DubatOlOV, V. V. & Kishida, Y. (2013) ReMarks On the species cOMpOsitiOn OF the genus Agrisius, With a descriptiOn OF a neW species FrOM LaOs (LepidOptera, Arctiidae: LithOsiinae). Tinea, 22 (3), 156 - 160.",
            "Daniel, F. (1952) Beitrage zur Kenntnis der Arctiidae Ostasiens unter besOnderer Berucksichtigung der Ausbeuten VOn Dr. h. c. H. Hone aus dieseM Gebiet (Lep. - Het.). Bonner zoologische Beitrage, 3 (1 - 2 & 3 - 4), 75 - 90 & 305 - 324.",
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
            {"start": "2002-03-01", "end": "2002-03-31", "type": "Collected"},
            {"start": "2003-06-01", "end": "2003-06-30", "type": "Collected"},
            {"start": "2004-05-24", "end": "2004-05-24", "type": "Collected"},
        ],
        # Misc
        "method": "A <em>very precise</em> scientific method was used...",
        # Custom
        "custom": {
            "dwc:scientificNameAuthorship": ["Volynkin & Dubatolov & Kishida"],
            "dwc:kingdom": ["Animalia"],
            "dwc:phylum": ["Arthropoda"],
            "dwc:order": ["Lepidoptera"],
            "dwc:family": ["Erebidae"],
            "dwc:genus": ["Agrisius"],
            "dwc:specificEpithet": ["japonicus"],
            "dwc:taxonomicStatus": ["stat. nov."],
            "dwc:taxonRank": ["subSpecies"],
            "dwc:collectionCode": ["SZMN"],
        },
    },
}
