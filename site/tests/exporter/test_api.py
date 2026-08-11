# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exporter integration tests."""

import csv
import gzip
import json
import tarfile
from uuid import uuid4

from invenio_files_rest.models import Bucket, ObjectVersion

from zenodo_rdm.exporter.tasks import export_records


def test_export_records_from_search_to_storage(
    running_app,
    publish_record,
    minimal_record,
    set_app_config_fn_scoped,
    tmp_path,
):
    """Publish complete export files from indexed records."""
    bucket_id = uuid4()
    set_app_config_fn_scoped(
        {
            "EXPORTER_BUCKET_UUID": bucket_id,
            "EXPORTER_STAGING_PATH": str(tmp_path),
        }
    )
    record = publish_record(dict(minimal_record, files={"enabled": False}))

    export_records(("json",), None)

    bucket = Bucket.get(bucket_id)
    assert bucket.quota_size is None
    assert bucket.max_file_size is None
    versions = ObjectVersion.get_by_bucket(bucket).all()
    assert {version.key for version in versions} == {
        "records-deleted.csv.gz",
        "records-json.tar.gz",
    }

    records = ObjectVersion.get(bucket, "records-json.tar.gz")
    with (
        records.file.storage().open() as stream,
        tarfile.open(fileobj=stream, mode="r:gz") as archive,
    ):
        members = archive.getmembers()
        assert [member.name for member in members] == [f"{record.id}.json"]
        exported = json.load(archive.extractfile(members[0]))
    assert exported["id"] == record.id
    assert exported["metadata"]["title"] == minimal_record["metadata"]["title"]

    deleted = ObjectVersion.get(bucket, "records-deleted.csv.gz")
    with (
        deleted.file.storage().open() as stream,
        gzip.open(stream, mode="rt") as uncompressed,
    ):
        assert list(csv.reader(uncompressed)) == [
            [
                "record_id",
                "doi",
                "parent_id",
                "parent_doi",
                "removal_note",
                "removal_reason",
                "removal_date",
                "citation_text",
            ]
        ]

    assert list(tmp_path.iterdir()) == []
