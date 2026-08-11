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
