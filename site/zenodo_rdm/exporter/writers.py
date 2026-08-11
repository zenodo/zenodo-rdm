# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write export files."""

import csv
import gzip
import json
import tarfile
from collections.abc import Iterable, Mapping, Sequence
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path

from flask import current_app
from invenio_rdm_records.oai import oai_datacite_etree
from lxml import etree

DELETED_HEADER = (
    "record_id",
    "doi",
    "parent_id",
    "parent_doi",
    "removal_note",
    "removal_reason",
    "removal_date",
    "citation_text",
)


def _serialize_json(record):
    return json.dumps(record).encode()


def _serialize_xml(record):
    tree = oai_datacite_etree(None, {"_source": record})
    return etree.tostring(
        tree,
        xml_declaration=True,
        encoding="UTF-8",
    )


SERIALIZERS = {
    "json": _serialize_json,
    "xml": _serialize_xml,
}
EXPORT_FORMATS = tuple(SERIALIZERS)


def write_archives(
    run_path: Path,
    formats: Sequence[str],
    records: Iterable[Mapping],
) -> list[Path]:
    """Write one set of records to all requested formats."""
    record_paths = {format: run_path / f"records-{format}.tar.gz" for format in formats}
    deleted_path = run_path / "records-deleted.csv.gz"

    with ExitStack() as stack:
        archives = {}
        for format, path in record_paths.items():
            stream = stack.enter_context(path.open("wb"))
            archives[format] = stack.enter_context(
                tarfile.open(fileobj=stream, mode="w|gz")
            )

        deleted = stack.enter_context(
            gzip.open(
                deleted_path,
                mode="wt",
                encoding="utf-8",
                newline="",
            )
        )
        deleted_writer = csv.writer(deleted)
        deleted_writer.writerow(DELETED_HEADER)

        for index, record in enumerate(records):
            if index % 1000 == 0:
                current_app.logger.debug(f"Record index: {index:_}")
            _write_record(record, formats, archives, deleted_writer)

    return [*record_paths.values(), deleted_path]


def _write_record(record, formats, archives, deleted_writer):
    record_id = record.get("id")
    if not record_id:
        return

    if record.get("deletion_status", {}).get("is_deleted", False):
        tombstone = record.get("tombstone", {})
        removal_reason = tombstone.get("removal_reason", {}).get("id")
        deleted_writer.writerow(
            [
                record_id,
                record["pids"]["doi"]["identifier"],
                record.get("parent", {}).get("id"),
                record.get("parent", {})
                .get("pids", {})
                .get("doi", {})
                .get("identifier"),
                tombstone.get("note"),
                removal_reason,
                tombstone.get("removal_date"),
                tombstone.get("citation_text") if removal_reason != "spam" else None,
            ]
        )
        return

    for format in formats:
        try:
            content = SERIALIZERS[format](record)
        except Exception:
            current_app.logger.exception(f"Could not serialize record: {record_id}")
            raise

        info = tarfile.TarInfo(f"{record_id}.{format}")
        info.size = len(content)
        archives[format].addfile(info, fileobj=BytesIO(content))
