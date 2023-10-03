# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions stream."""

from uuid import UUID

import pytest
import sqlalchemy as sa
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.files import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)
from invenio_rdm_migrator.streams.models.pids import PersistentIdentifier
from invenio_rdm_migrator.streams.models.records import (
    RDMDraftFile,
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMRecordFile,
    RDMRecordMetadata,
    RDMVersionState,
)
from sqlalchemy.orm import Session


@pytest.fixture()
def draft(
    database,
    session: Session,
    test_extract_cls,
    tx_transform,
    pg_tx_load,
    tx_files,
):
    """Draft fixture via actions load."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["create"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()


@pytest.fixture()
def draft_with_file(
    database,
    draft,
    session: Session,
    test_extract_cls,
    tx_transform,
    pg_tx_load,
    tx_files,
):
    """Draft with file fixture via actions load."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["file-upload"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()


@pytest.fixture()
def full_draft(
    database,
    draft_with_file,
    session: Session,
    test_extract_cls,
    tx_transform,
    pg_tx_load,
    tx_files,
):
    """Draft with file fixture via actions load."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["update"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()


@pytest.fixture()
def published_record(
    database,
    full_draft,
    session: Session,
    test_extract_cls,
    tx_transform,
    pg_tx_load,
    tx_files,
):
    """Published draft via actions load."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["publish-new"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()


@pytest.fixture()
def edited_record(
    database,
    published_record,
    session: Session,
    test_extract_cls,
    tx_transform,
    pg_tx_load,
    tx_files,
):
    """Published draft via actions load."""
    stream = Stream(
        name="action",
        extract=test_extract_cls([tx_files["edit"], tx_files["edit-update"]]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()


def test_draft_create(
    database,
    session: Session,
    test_extract_cls,
    pg_tx_load,
    tx_transform,
    tx_files,
):
    """Test draft create action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["create"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()

    # PIDs
    pids = {
        p.pid_value: p for p in session.scalars(sa.select(PersistentIdentifier)).all()
    }
    assert len(pids) == 2
    pid = pids["1243808"]
    assert pid.object_type == "rec"
    assert pid.status == "R"
    assert pid.pid_type == "recid"

    parent_pid = pids["1243807"]
    assert parent_pid.object_type == "rec"
    assert parent_pid.status == "R"
    assert parent_pid.pid_type == "recid"

    # Bucket
    bucket = session.scalars(sa.select(FilesBucket)).one()
    assert bucket.id == UUID("3ee8b44d-3852-4644-a7e4-693689bcaad6")

    # Draft parent and versioning
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    assert draft.bucket_id == bucket.id
    assert draft.fork_version_id is None
    assert draft.index == 1
    assert draft.id == pid.object_uuid
    assert draft.json["id"] == "1243808"
    assert draft.json["pid"] == {
        "pk": 1,
        "obj_type": "rec",
        "pid_type": "recid",
        "status": "R",
    }
    assert draft.json["files"] == {"enabled": True}
    assert draft.json["media_files"] == {"enabled": False}
    assert draft.json["$schema"] == "local://records/record-v6.0.0.json"
    assert draft.json["access"] == {"files": "public", "record": "public"}
    assert draft.json["custom_fields"] == {}

    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    assert parent.id == parent_pid.object_uuid
    assert draft.parent_id == parent.id
    assert parent.json["id"] == "1243807"
    assert parent.json["pid"]["pk"] == 2
    assert parent.json["pid"] == {
        "pk": 2,
        "obj_type": "rec",
        "pid_type": "recid",
        "status": "R",
    }
    assert parent.json["access"] == {"owned_by": {"user": 22858}}

    versioning = session.scalars(sa.select(RDMVersionState)).one()
    assert parent.id == draft.parent_id == versioning.parent_id
    assert draft.id == versioning.next_draft_id
    assert versioning.latest_id is None
    assert versioning.latest_index is None


def test_draft_update(
    database,
    session: Session,
    draft,
    test_extract_cls,
    pg_tx_load,
    tx_files,
    tx_transform,
):
    """Test draft update action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["update"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()

    # Draft parent and versioning
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    pids = {
        p.pid_value: p for p in session.scalars(sa.select(PersistentIdentifier)).all()
    }
    assert len(pids) == 2
    assert draft.fork_version_id is None
    assert draft.json["id"] == "1243808"
    assert draft.json["pid"] == {
        "pk": pids["1243808"].id,
        "obj_type": "rec",
        "pid_type": "recid",
        "status": "R",
    }
    assert draft.json["pids"] == {}
    assert draft.json["metadata"] == {
        "additional_descriptions": [
            {"description": "This is a note", "type": {"id": "notes"}},
        ],
        "creators": [
            {
                "person_or_org": {
                    "family_name": "Alex",
                    "name": "Alex",
                    "type": "personal",
                },
            },
        ],
        "publisher": "Zenodo",
        "description": "<p>Initial update title</p>",
        "languages": [{"id": "eng"}],
        "publication_date": "2023-09-29",
        "resource_type": {
            "id": "publication-article",
        },
        "rights": [{"id": "cc-by-4.0"}],
        "subjects": [
            {"subject": "science"},
            {"subject": "maths"},
        ],
        "title": "Initial update title",
        "version": "v1.0.0",
    }
    assert draft.json["custom_fields"] == {}

    assert draft.json["files"] == {"enabled": True}
    assert draft.json["media_files"] == {"enabled": False}
    assert draft.json["$schema"] == "local://records/record-v6.0.0.json"
    assert draft.json["access"] == {"files": "public", "record": "public"}

    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    assert draft.parent_id == parent.id
    assert parent.json == {
        "$schema": "local://records/parent-v3.0.0.json",
        "communities": {},
        "access": {"owned_by": {"user": 22858}},
        "id": "1243807",
        "pid": {
            "obj_type": "rec",
            "pid_type": "recid",
            "pk": pids["1243807"].id,
            "status": "R",
        },
        "pids": {},
    }


def test_draft_file_upload(
    database,
    session: Session,
    draft,
    test_extract_cls,
    pg_tx_load,
    tx_files,
    tx_transform,
):
    """Test draft file upload action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["file-upload"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()

    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    bucket = session.scalars(sa.select(FilesBucket)).one()
    file = session.scalars(sa.select(FilesInstance)).one()
    ov = session.scalars(sa.select(FilesObjectVersion)).one()
    assert ov.bucket_id == bucket.id == draft.bucket_id
    assert ov.is_head
    assert ov.file_id == file.id
    draft_file = session.scalars(sa.select(RDMDraftFile)).one()
    assert draft_file.record_id == draft.id
    assert draft_file.object_version_id == ov.version_id
    assert ov.key == draft_file.key == "article.pdf"
    assert draft_file.json == {}


def test_draft_publish_new(
    database,
    session: Session,
    full_draft,
    test_extract_cls,
    pg_tx_load,
    tx_files,
    tx_transform,
):
    """Test draft publish new action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["publish-new"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()

    # Record/draft/parent
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    record = session.scalars(sa.select(RDMRecordMetadata)).one()
    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    versioning = session.scalars(sa.select(RDMVersionState)).one()

    assert draft.json is None
    assert draft.fork_version_id is None
    assert record.index == 1
    assert record.deletion_status == "P"
    assert versioning.parent_id == parent.id
    assert versioning.latest_id == record.id
    assert versioning.latest_index == record.index
    assert versioning.next_draft_id is None

    # PIDs
    pids = {
        p.pid_value: p for p in session.scalars(sa.select(PersistentIdentifier)).all()
    }
    assert len(pids) == 5
    oai_pid = pids["oai:zenodo.org:1243808"]
    doi = pids["10.5072/zenodo.1243808"]
    parent_doi = pids["10.5072/zenodo.1243807"]
    pid = pids["1243808"]
    parent_pid = pids["1243807"]
    assert (
        pid.status
        == doi.status
        == parent_doi.status
        == oai_pid.status
        == parent_pid.status
        == "R"
    )
    assert (
        pid.object_uuid
        == doi.object_uuid
        == oai_pid.object_uuid
        == record.id
        == draft.id
    )
    assert parent_doi.object_uuid == parent_pid.object_uuid == parent.id
    assert record.json["pids"] == {
        "oai": {
            "provider": "oai",
            "identifier": oai_pid.pid_value,
        },
        "doi": {
            "client": "datacite",
            "provider": "datacite",
            "identifier": doi.pid_value,
        },
    }
    assert parent.json["pids"] == {
        "doi": {
            "client": "datacite",
            "provider": "datacite",
            "identifier": parent_doi.pid_value,
        },
    }

    # Files
    buckets = {b.id: b for b in session.scalars(sa.select(FilesBucket)).all()}
    assert len(buckets) == 2
    draft_bucket = buckets[draft.bucket_id]
    record_bucket = buckets[record.bucket_id]
    assert draft_bucket != record_bucket
    assert draft_bucket.locked is True
    assert record_bucket.locked is True

    file = session.scalars(sa.select(FilesInstance)).one()
    assert file
    ovs = {
        (ov.bucket_id, ov.key): ov
        for ov in session.scalars(sa.select(FilesObjectVersion)).all()
    }
    assert len(ovs) == 2
    draft_ov = ovs[(draft.bucket_id, "article.pdf")]
    record_ov = ovs[(record.bucket_id, "article.pdf")]
    assert draft_ov != record_ov
    assert draft_ov.file_id == record_ov.file_id == file.id
    assert draft_ov.is_head
    assert record_ov.is_head

    draft_file = session.scalars(sa.select(RDMDraftFile)).one()
    assert draft_file.record_id == draft.id
    assert draft_file.object_version_id == draft_ov.version_id
    record_file = session.scalars(sa.select(RDMRecordFile)).one()
    assert record_file.record_id == record.id
    assert record_file.object_version_id == record_ov.version_id
    assert (
        draft_ov.key
        == draft_file.key
        == record_file.key
        == record_ov.key
        == "article.pdf"
    )
    assert draft_file.json == record_file.json == {}


def test_draft_edit(
    database,
    session: Session,
    published_record,
    test_extract_cls,
    pg_tx_load,
    tx_files,
    tx_transform,
):
    """Test draft edit action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["edit"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()

    # Record/draft/parent
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    record = session.scalars(sa.select(RDMRecordMetadata)).one()
    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    assert draft.fork_version_id == record.version_id

    # PIDs
    pids = {
        p.pid_value: p for p in session.scalars(sa.select(PersistentIdentifier)).all()
    }
    assert len(pids) == 5
    oai_pid = pids["oai:zenodo.org:1243808"]
    doi = pids["10.5072/zenodo.1243808"]
    parent_doi = pids["10.5072/zenodo.1243807"]
    pid = pids["1243808"]
    parent_pid = pids["1243807"]
    assert (
        pid.status
        == doi.status
        == parent_doi.status
        == oai_pid.status
        == parent_pid.status
        == "R"
    )
    assert (
        pid.object_uuid
        == doi.object_uuid
        == oai_pid.object_uuid
        == record.id
        == draft.id
    )
    assert parent_doi.object_uuid == parent_pid.object_uuid == parent.id

    # Files
    buckets = {b.id: b for b in session.scalars(sa.select(FilesBucket)).all()}
    assert len(buckets) == 2
    draft_bucket = buckets[draft.bucket_id]
    record_bucket = buckets[record.bucket_id]
    assert draft_bucket != record_bucket
    assert draft_bucket.locked is True
    assert record_bucket.locked is True

    file = session.scalars(sa.select(FilesInstance)).one()
    assert file
    ovs = {
        (ov.bucket_id, ov.key): ov
        for ov in session.scalars(sa.select(FilesObjectVersion)).all()
    }
    assert len(ovs) == 2
    draft_ov = ovs[(draft.bucket_id, "article.pdf")]
    record_ov = ovs[(record.bucket_id, "article.pdf")]
    assert draft_ov != record_ov
    assert draft_ov.file_id == record_ov.file_id == file.id
    assert draft_ov.is_head
    assert record_ov.is_head

    draft_file = session.scalars(sa.select(RDMDraftFile)).one()
    assert draft_file.record_id == draft.id
    assert draft_file.object_version_id == draft_ov.version_id
    record_file = session.scalars(sa.select(RDMRecordFile)).one()
    assert record_file.record_id == record.id
    assert record_file.object_version_id == record_ov.version_id
    assert (
        draft_ov.key
        == draft_file.key
        == record_file.key
        == record_ov.key
        == "article.pdf"
    )
    assert draft_file.json == record_file.json == {}

    assert draft.json == {
        "$schema": "local://records/record-v6.0.0.json",
        "access": {
            "files": "public",
            "record": "public",
        },
        "custom_fields": {},
        "files": {"enabled": True},
        "id": "1243808",
        "media_files": {"enabled": False},
        "metadata": {
            "additional_descriptions": [
                {
                    "description": "This is a note",
                    "type": {"id": "notes"},
                },
            ],
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Alex",
                        "name": "Alex",
                        "type": "personal",
                    },
                },
            ],
            "description": "<p>Initial update title</p>",
            "languages": [{"id": "eng"}],
            "publication_date": "2023-09-29",
            "publisher": "Zenodo",
            "resource_type": {
                "id": "publication-article",
            },
            "rights": [{"id": "cc-by-4.0"}],
            "subjects": [
                {"subject": "science"},
                {"subject": "maths"},
            ],
            "title": "Initial update title",
            "version": "v1.0.0",
        },
        "pid": {
            "obj_type": "rec",
            "pid_type": "recid",
            "pk": pid.id,
            "status": "R",
        },
        "pids": {
            "doi": {
                "client": "datacite",
                "identifier": "10.5072/zenodo.1243808",
                "provider": "datacite",
            },
            "oai": {
                "identifier": "oai:zenodo.org:1243808",
                "provider": "oai",
            },
        },
    }


def test_draft_publish_edit(
    database,
    session: Session,
    edited_record,
    test_extract_cls,
    pg_tx_load,
    tx_files,
    tx_transform,
):
    """Test draft edit action."""
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["publish-edit"]),
        transform=tx_transform,
        load=pg_tx_load,
    )
    stream.run()

    # Record/draft/parent
    draft = session.scalars(sa.select(RDMDraftMetadata)).one()
    record = session.scalars(sa.select(RDMRecordMetadata)).one()
    parent = session.scalars(sa.select(RDMParentMetadata)).one()
    versioning = session.scalars(sa.select(RDMVersionState)).one()
    assert draft.fork_version_id is None
    assert draft.json is None
    assert draft.fork_version_id is None
    assert record.index == 1
    assert record.deletion_status == "P"
    assert versioning.parent_id == parent.id
    assert versioning.latest_id == record.id
    assert versioning.latest_index == record.index
    assert versioning.next_draft_id is None

    # PIDs
    pids = {
        p.pid_value: p for p in session.scalars(sa.select(PersistentIdentifier)).all()
    }
    assert len(pids) == 5
    oai_pid = pids["oai:zenodo.org:1243808"]
    doi = pids["10.5072/zenodo.1243808"]
    parent_doi = pids["10.5072/zenodo.1243807"]
    pid = pids["1243808"]
    parent_pid = pids["1243807"]
    assert (
        pid.status
        == doi.status
        == parent_doi.status
        == oai_pid.status
        == parent_pid.status
        == "R"
    )
    assert (
        pid.object_uuid
        == doi.object_uuid
        == oai_pid.object_uuid
        == record.id
        == draft.id
    )
    assert parent_doi.object_uuid == parent_pid.object_uuid == parent.id

    # Files
    buckets = {b.id: b for b in session.scalars(sa.select(FilesBucket)).all()}
    assert len(buckets) == 2
    draft_bucket = buckets[draft.bucket_id]
    record_bucket = buckets[record.bucket_id]
    assert draft_bucket != record_bucket
    assert draft_bucket.locked is True
    assert record_bucket.locked is True

    file = session.scalars(sa.select(FilesInstance)).one()
    assert file
    ovs = {
        (ov.bucket_id, ov.key): ov
        for ov in session.scalars(sa.select(FilesObjectVersion)).all()
    }
    assert len(ovs) == 2
    draft_ov = ovs[(draft.bucket_id, "article.pdf")]
    record_ov = ovs[(record.bucket_id, "article.pdf")]
    assert draft_ov != record_ov
    assert draft_ov.file_id == record_ov.file_id == file.id
    assert draft_ov.is_head
    assert record_ov.is_head

    draft_file = session.scalars(sa.select(RDMDraftFile)).one()
    assert draft_file.record_id == draft.id
    assert draft_file.object_version_id == draft_ov.version_id
    record_file = session.scalars(sa.select(RDMRecordFile)).one()
    assert record_file.record_id == record.id
    assert record_file.object_version_id == record_ov.version_id
    assert (
        draft_ov.key
        == draft_file.key
        == record_file.key
        == record_ov.key
        == "article.pdf"
    )
    assert draft_file.json == record_file.json == {}

    assert record.json == {
        "$schema": "local://records/record-v6.0.0.json",
        "access": {
            "files": "public",
            "record": "public",
        },
        "custom_fields": {},
        "files": {"enabled": True},
        "id": "1243808",
        "media_files": {"enabled": False},
        "metadata": {
            "additional_descriptions": [
                {
                    "description": "This is a note",
                    "type": {"id": "notes"},
                },
            ],
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Alex",
                        "name": "Alex",
                        "type": "personal",
                    },
                },
            ],
            "description": "<p>Initial edit title</p>",
            "languages": [{"id": "eng"}],
            "publication_date": "2023-09-29",
            "publisher": "Zenodo",
            "resource_type": {
                "id": "publication-article",
            },
            "rights": [{"id": "cc-by-4.0"}],
            "subjects": [
                {"subject": "science"},
                {"subject": "maths"},
                {"subject": "open"},
            ],
            "title": "Initial edit title",
            "version": "v1.0.0",
        },
        "pid": {
            "obj_type": "rec",
            "pid_type": "recid",
            "pk": pid.id,
            "status": "R",
        },
        "pids": {
            "doi": {
                "client": "datacite",
                "identifier": "10.5072/zenodo.1243808",
                "provider": "datacite",
            },
            "oai": {
                "identifier": "oai:zenodo.org:1243808",
                "provider": "oai",
            },
        },
    }
