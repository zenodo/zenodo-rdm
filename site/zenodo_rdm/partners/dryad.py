# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Dryad payloads and settings."""

PAYLOAD = {
    "metadata": {
        # Communities
        # "communities": [{"identifier": "dryad"}],
        #
        # Required/basic fields
        #
        # Resource type
        # "upload_type": "dataset",
        # "upload_type": "software",
        "upload_type": "other",
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
        "keywords": [
            "cell biology",
            "machine learning",
            "cancer",
            "Open-source",
            "software",
            "phenotyping",
            "automation",
            "image analysis",
        ],
        "notes": "<p>ROI files can be opened with ImageJ. Image .tif files can be opened with any imaging software including ImageJ. Feature tables are provided as comma separated files and can be opened with Excel, for example.</p><p>Funding provided by: Biotechnology and Biological Sciences Research Council<br>Crossref Funder Registry ID: http://dx.doi.org/10.13039/501100000268<br>Award Number: BB/S507416/1</p>",
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
                "scheme": "url",
                "identifier": "https://www.researchsquare.com/article/rs-971415/v1",
                "relation": "isCitedBy",
            },
            {
                "scheme": "doi",
                "identifier": "10.5281/zenodo.7620171",
                "relation": "isDerivedFrom",
            },
            {
                "scheme": "url",
                "identifier": "https://cellphegui.shinyapps.io/app_to_host/",
                "relation": "isDerivedFrom",
            },
            {
                "scheme": "doi",
                "identifier": "10.5061/dryad.4xgxd25f0",
                "relation": "isDerivedFrom",
            },
        ],
        # Locations
        "locations": [
            {"lat": 32.898114, "place": "San Diego, CA 92121, USA", "lon": -117.202936},
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
    }
}
