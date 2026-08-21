# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exporter writer tests."""

import csv
import gzip
import json
import tarfile

from zenodo_rdm.exporter.writers import write_archives


def _tar_members(path):
    with tarfile.open(path, mode="r:gz") as archive:
        return {
            member.name: archive.extractfile(member).read()
            for member in archive.getmembers()
        }


def test_write_export_files(app, tmp_path):
    """Write complete record and deletion files."""
    records = [
        {"id": "active", "metadata": {"title": "Test"}},
        {
            "id": "deleted",
            "deletion_status": {"is_deleted": True},
            "pids": {"doi": {"identifier": "10.5281/zenodo.1"}},
            "parent": {},
            "tombstone": {"removal_reason": {"id": "spam"}},
        },
    ]

    with app.app_context():
        paths = write_archives(tmp_path, ("json",), records)

    assert [path.name for path in paths] == [
        "records-json.tar.gz",
        "records-deleted.csv.gz",
    ]
    members = _tar_members(paths[0])
    assert json.loads(members["active.json"]) == records[0]
    assert "deleted.json" not in members

    with gzip.open(paths[1], mode="rt") as stream:
        rows = list(csv.reader(stream))
    assert rows[1][0:2] == ["deleted", "10.5281/zenodo.1"]


def test_write_consumes_records_once_for_all_outputs(app, tmp_path):
    """One record pass writes every requested format."""
    iterations = []

    def records():
        iterations.append("started")
        yield {
            "id": "deleted",
            "deletion_status": {"is_deleted": True},
            "pids": {"doi": {"identifier": "10.5281/zenodo.1"}},
            "parent": {},
            "tombstone": {"removal_reason": {"id": "spam"}},
        }

    with app.app_context():
        paths = write_archives(tmp_path, ("json", "xml"), records())

    assert iterations == ["started"]
    assert _tar_members(paths[0]) == {}
    assert _tar_members(paths[1]) == {}


def test_write_continues_after_record_errors(app, tmp_path, minimal_record, caplog):
    """Malformed records do not stop other records or formats."""
    invalid_xml = dict(
        minimal_record,
        id="invalid-xml",
        metadata=dict(
            minimal_record["metadata"],
            funding=[
                {
                    "funder": {"name": "Test funder"},
                    "award": {"title": {"en": "Invalid\x00title"}},
                }
            ],
        ),
    )
    records = [
        invalid_xml,
        {
            "id": "deleted",
            "deletion_status": {"is_deleted": True},
            "pids": {"doi": {"identifier": "10.5281/zenodo.1"}},
            "parent": None,
            "tombstone": None,
        },
        {"id": "after-error", "metadata": {"title": "Test"}},
    ]

    with app.app_context():
        paths = write_archives(tmp_path, ("json", "xml"), records)

    json_members = _tar_members(paths[0])
    xml_members = _tar_members(paths[1])
    assert set(json_members) == {"invalid-xml.json", "after-error.json"}
    assert "invalid-xml.xml" not in xml_members
    assert "Could not serialize record invalid-xml as xml" in caplog.text

    with gzip.open(paths[2], mode="rt") as stream:
        rows = list(csv.reader(stream))
    assert rows[1][0:2] == ["deleted", "10.5281/zenodo.1"]
