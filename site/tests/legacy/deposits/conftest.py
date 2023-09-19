# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Deposit fixtures."""

from datetime import datetime, timedelta

import pytest


@pytest.fixture(scope="function")
def test_data():
    """Returns deposit data."""
    return dict(
        metadata=dict(
            access_right="embargoed",
            communities=[{"identifier": "c1"}],
            conference_acronym="Some acronym",
            conference_dates="Some dates",
            conference_place="Some place",
            conference_title="Some title",
            conference_url="http://someurl.com",
            conference_session="VI",
            conference_session_part="1",
            creators=[
                dict(
                    name="Doe, John",
                    affiliation="Atlantis",
                    orcid="0000-0002-1825-0097",
                    gnd="170118215",
                ),
                dict(name="Smith, Jane", affiliation="Atlantis"),
            ],
            description="Some description",
            doi="10.1234/foo.bar",
            embargo_date=(datetime.utcnow().date() + timedelta(days=1)).isoformat(),
            grants=[
                dict(id="10.13039/501100001665::755021"),
            ],
            # NOTE: changed previous string ("Some isbn") to a valid isbn
            imprint_isbn="978-3-16-148410-0",
            imprint_place="Some place",
            # TODO changed previous string ("Some publisher") to "Zenodo" which is the hardcoded publisher for now.
            imprint_publisher="Zenodo",
            journal_issue="Some issue",
            journal_pages="Some pages",
            journal_title="Some journal name",
            journal_volume="Some volume",
            keywords=["Keyword 1", "keyword 2"],
            subjects=[
                dict(scheme="gnd", identifier="gnd:1234567899", term="Astronaut"),
                dict(scheme="gnd", identifier="gnd:1234567898", term="Amish"),
            ],
            license="CC0-1.0",
            notes="Some notes",
            partof_pages="SOme part of",
            partof_title="Some part of title",
            prereserve_doi=True,
            publication_date="2013-09-12",
            publication_type="book",
            references=[
                "Reference 1",
                "Reference 2",
            ],
            related_identifiers=[
                dict(identifier="10.1234/foo.bar2", relation="isCitedBy", scheme="doi"),
                dict(
                    identifier="10.1234/foo.bar3",
                    relation="cites",
                    scheme="doi",
                    resource_type="dataset",
                ),
                dict(
                    identifier="2011ApJS..192...18K",
                    relation="isAlternateIdentifier",
                    scheme="ads",
                ),
            ],
            thesis_supervisors=[
                dict(name="Doe, John", affiliation="Atlantis"),
                dict(
                    name="Smith, Jane",
                    affiliation="Atlantis",
                    orcid="0000-0002-1825-0097",
                    gnd="170118215",
                ),
            ],
            thesis_university="Some thesis_university",
            contributors=[
                dict(name="Doe, Jochen", affiliation="Atlantis", type="Other"),
                dict(
                    name="Smith, Marco",
                    affiliation="Atlantis",
                    orcid="0000-0002-1825-0097",
                    gnd="170118215",
                    type="DataCurator",
                ),
            ],
            locations=[
                dict(
                    place="London",
                    description="A nice location",
                    lat=10.2,
                    lon=5,
                ),
                dict(place="Lisbon", lat=5.1231221, lon=1.23232323),
            ],
            title="Test title",
            upload_type="publication",
        )
    )


@pytest.fixture(scope="function")
def expected_record_metadata():
    """Return expected rdm draft metadata."""
    return dict(
        access_right="embargoed",
        communities=[{"identifier": "c1"}],
        conference_acronym="Some acronym",
        conference_dates="Some dates",
        conference_place="Some place",
        conference_title="Some title",
        conference_url="http://someurl.com",
        conference_session="VI",
        conference_session_part="1",
        creators=[
            dict(
                name="Doe, John",
                affiliation="Atlantis",
                orcid="0000-0002-1825-0097",
                gnd="170118215",
            ),
            dict(name="Smith, Jane", affiliation="Atlantis"),
        ],
        description="Some description",
        embargo_date=(datetime.utcnow().date() + timedelta(days=1)).isoformat(),
        grants=[
            dict(id="10.13039/501100001665::755021"),
        ],
        imprint_isbn="978-3-16-148410-0",
        imprint_place="Some place",
        imprint_publisher="Zenodo",
        journal_issue="Some issue",
        journal_pages="Some pages",
        journal_title="Some journal name",
        journal_volume="Some volume",
        keywords=["Keyword 1", "keyword 2"],
        subjects=[
            dict(scheme="gnd", identifier="gnd:1234567899", term="Astronaut"),
            dict(scheme="gnd", identifier="gnd:1234567898", term="Amish"),
        ],
        license="cc-zero",
        notes="Some notes",
        partof_pages="SOme part of",
        partof_title="Some part of title",
        prereserve_doi=True,
        publication_date="2013-09-12",
        publication_type="book",
        references=[
            "Reference 1",
            "Reference 2",
        ],
        related_identifiers=[
            dict(identifier="10.1234/foo.bar2", relation="isCitedBy", scheme="doi"),
            dict(
                identifier="10.1234/foo.bar3",
                relation="cites",
                scheme="doi",
                resource_type="dataset",
            ),
            dict(
                identifier="2011ApJS..192...18K",
                relation="isAlternateIdentifier",
                scheme="ads",
            ),
        ],
        thesis_university="Some thesis_university",
        contributors=[
            dict(name="Doe, John", affiliation="Atlantis", type="Supervisor"),
            dict(
                name="Smith, Jane",
                affiliation="Atlantis",
                orcid="0000-0002-1825-0097",
                gnd="170118215",
                type="Supervisor",
            ),
            dict(name="Doe, Jochen", affiliation="Atlantis", type="Other"),
            dict(
                name="Smith, Marco",
                affiliation="Atlantis",
                orcid="0000-0002-1825-0097",
                gnd="170118215",
                type="DataCurator",
            ),
            # It was agreed that thesis_supervisors should not be returned, in favor of 'contributors'.
            # See https://github.com/zenodo/zenodo-rdm/pull/289
        ],
        locations=[
            dict(
                place="London",
                description="A nice location",
                lat=10.2,
                lon=5,
            ),
            dict(place="Lisbon", lat=5.1231221, lon=1.23232323),
        ],
        title="Test title",
        upload_type="publication",
    )
