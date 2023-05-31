# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Test deposit api."""

import json
from datetime import datetime, timedelta

import dictdiffer
import pytest

from zenodo_rdm.legacy.resources import LegacyRecordResourceConfig


@pytest.fixture(scope="function")
def test_data():
    return dict(
        metadata=dict(
            access_right="embargoed",
            # TODO uncomment when communities are implemented
            # communities=[{"identifier": "c1"}],
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
            # TODO changed previous string ("Some isbn") to a valid isbn
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
                # TODO commented since scheme ads not supported in rdm
                # dict(
                #     identifier="2011ApJS..192...18K",
                #     relation="isAlternateIdentifier",
                #     scheme="ads",
                #     resource_type="publication-article",
                # ),
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
    return dict(
        access_right="embargoed",
        # TODO uncomment when communities are implemented
        # communities=[{"identifier": "c1"}],
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
        # TODO uncomment when subjects are implemented
        # subjects=[
        #     dict(scheme="gnd", identifier="gnd:1234567899", term="Astronaut"),
        #     dict(scheme="gnd", identifier="gnd:1234567898", term="Amish"),
        # ],
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


@pytest.fixture
def get_json():
    """Function for extracting json from response."""

    def inner(response, code=None):
        """Decode JSON from response."""
        data = response.get_data(as_text=True)
        if code is not None:
            assert response.status_code == code, data
        return json.loads(data)

    return inner


@pytest.fixture
def deposit_url():
    """Deposit API URL."""
    return f"/api{LegacyRecordResourceConfig.url_prefix}"


def test_invalid_create(test_app, client_with_login, deposit_url, headers):
    """Test invalid deposit creation.

    Test ported from https://github.com/zenodo/zenodo/blob/master/tests/unit/deposit/test_api_metadata.py.
    """
    client = client_with_login

    # Invalid deposits.
    cases = [
        dict(unknownkey="data", metadata={}),
        dict(metadata={}),
    ]

    for case in cases:
        res = client.post(deposit_url, data=json.dumps(case), headers=headers)
        assert res.status_code == 400, case

    # No deposits were created
    res = client.get(deposit_url, headers=headers)
    assert res.json["hits"]["total"] == 0


def test_input_output(
    test_app,
    client_with_login,
    headers,
    deposit_url,
    get_json,
    test_data,
    expected_record_metadata,
):
    """Rough validation of input against output data.

    Test ported from https://github.com/zenodo/zenodo/blob/master/tests/unit/deposit/test_api_metadata.py.
    """
    client = client_with_login

    # Create
    res = client.post(deposit_url, data=json.dumps(test_data), headers=headers)
    links = get_json(res, code=201)["links"]

    # Get serialization.
    data = get_json(client.get(links["self"], headers=headers), code=200)

    # - fix known differences.
    # DOI and recid have 2 as control number, since Concept DOI/recid are
    # registered first
    recid = data["id"]
    expected_record_metadata.update(
        {
            "prereserve_doi": {"doi": f"10.5281/zenodo.{recid}", "recid": recid},
        }
    )

    ignored_keys = set()

    # doi is returned as a top level key (and not inside metadata)
    assert data["doi"] == test_data["metadata"]["doi"]
    ignored_keys.add("doi")

    differences = list(
        dictdiffer.diff(data["metadata"], expected_record_metadata, ignore=ignored_keys)
    )

    assert not differences
