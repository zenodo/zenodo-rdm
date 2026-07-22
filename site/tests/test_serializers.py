# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration tests for serializers."""


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
