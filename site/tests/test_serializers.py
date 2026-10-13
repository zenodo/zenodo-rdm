# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for serializers."""

import pytest

from zenodo_rdm.legacy.serializers.schemas.zenodojson import MetadataSchema


def test_datacite_serializer(app, publish_record, minimal_record, mocker):
    """Test that DOI minting includes the parent DOI as a related identifier."""
    base = dict(minimal_record, files={"enabled": False})
    metadata = dict(
        base,
        metadata=dict(
            base["metadata"],
            resource_type={"id": "publication-dissertation"},
            title="A thesis",
        ),
    )
    title = metadata["metadata"]["title"]
    first_name = metadata["metadata"]["creators"][0]["person_or_org"]["given_name"]

    mocker.patch("tests.fake_datacite_client.FakeDataCiteRESTClient.public_doi")

    record = publish_record(metadata)
    record_pid = record._record.pid.pid_value
    concept_pid = record._record.parent.pid.pid_value
    record_doi = f"10.5281/zenodo.{record_pid}"
    concept_doi = f"10.5281/zenodo.{concept_pid}"

    config = app.config["RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS"]
    public_doi_fn = config[0].client._api.public_doi
    # # get the metadata value
    assert public_doi_fn.call_count == 2
    # the first call is for the record DOI
    serialized_record = public_doi_fn.call_args_list[0].kwargs["metadata"]
    # the second call is for the concept DOI
    serialized_concept = public_doi_fn.call_args_list[1].kwargs["metadata"]

    for record in [serialized_record, serialized_concept]:
        assert record["titles"][0]["title"] == title
        assert record["creators"][0]["givenName"] == first_name

    assert serialized_record["doi"] == record_doi
    assert len(serialized_record["relatedIdentifiers"]) == 1
    first_related_identifier = serialized_record["relatedIdentifiers"][0]
    # the record is a version of the concept DOI
    assert first_related_identifier["relatedIdentifier"] == concept_doi
    assert first_related_identifier["relationType"] == "IsVersionOf"
    assert first_related_identifier["relatedIdentifierType"] == "DOI"

    assert serialized_concept["doi"] == concept_doi
    assert len(serialized_concept["relatedIdentifiers"]) == 1
    first_related_identifier = serialized_concept["relatedIdentifiers"][0]
    # the concept has version of records
    assert first_related_identifier["relatedIdentifier"] == record_doi
    assert first_related_identifier["relationType"] == "HasVersion"
    assert first_related_identifier["relatedIdentifierType"] == "DOI"


@pytest.mark.parametrize(
    "geometry, expected_coordinates",
    [
        ({"type": "Point", "coordinates": [8.55, 47.37]}, {"lon": 8.55, "lat": 47.37}),
        ({"type": "Point", "coordinates": [0, 0]}, {"lon": 0, "lat": 0}),
        (
            {"type": "Point", "coordinates": [8.55, 47.37, 400]},
            {"lon": 8.55, "lat": 47.37},
        ),
        ({"type": "Point", "coordinates": [8.55]}, {}),
        ({"type": "Point", "coordinates": []}, {}),
        ({}, {}),
        (
            {
                "type": "Polygon",
                "coordinates": [[[8, 47], [9, 47], [9, 48], [8, 47]]],
            },
            {},
        ),
        ({"type": "MultiPoint", "coordinates": [[8, 47], [9, 48]]}, {}),
    ],
)
def test_legacy_locations_preserve_text_and_only_export_point_coordinates(
    app, geometry, expected_coordinates
):
    """Legacy locations retain text without misrepresenting non-point geometry."""
    metadata = {
        "locations": {
            "features": [
                {
                    "place": "Zurich",
                    "description": "Study area",
                    "geometry": geometry,
                }
            ]
        }
    }
    with app.app_context():
        result = MetadataSchema(only=("locations",)).dump(metadata)

    assert result["locations"] == [
        {"place": "Zurich", "description": "Study area", **expected_coordinates}
    ]
