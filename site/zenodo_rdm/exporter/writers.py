# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write export files."""

import csv
import gzip
import json
import tarfile
import time
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


def _format_duration(seconds):
    """Format a duration for progress logs."""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _log_progress(processed, total, started, errors, completed=False):
    """Log export progress and throughput."""
    elapsed = max(time.monotonic() - started, 1e-9)
    rate = processed / elapsed
    if completed:
        current_app.logger.info(
            "Exporter completed: processed %s/%s records in %s at %s records/s "
            "with %s errors",
            f"{processed:_}",
            f"{total:_}",
            _format_duration(elapsed),
            f"{rate:,.1f}",
            f"{errors:_}",
        )
        return

    percentage = processed / total * 100 if total else 100
    remaining = max(total - processed, 0) / rate if rate else 0
    current_app.logger.info(
        "Processed %s/%s records (%.1f%%) at %s records/s; ETA %s; errors: %s",
        f"{processed:_}",
        f"{total:_}",
        percentage,
        f"{rate:,.1f}",
        _format_duration(remaining),
        f"{errors:_}",
    )


def write_archives(
    run_path: Path,
    formats: Sequence[str],
    records: Iterable[Mapping],
    total: int,
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

        started = time.monotonic()
        processed = 0
        errors = 0
        for processed, record in enumerate(records, start=1):
            errors += _write_record(record, formats, archives, deleted_writer)
            if processed % 1000 == 0:
                _log_progress(processed, total, started, errors)

        _log_progress(processed, total, started, errors, completed=True)

    return [*record_paths.values(), deleted_path]


def _write_record(record, formats, archives, deleted_writer):
    record_id = record.get("id")
    if not record_id:
        current_app.logger.error("Could not export record without an id")
        return 1

    if (record.get("deletion_status") or {}).get("is_deleted", False):
        try:
            tombstone = record.get("tombstone") or {}
            removal_reason = (tombstone.get("removal_reason") or {}).get("id")
            parent = record.get("parent") or {}
            row = [
                record_id,
                record["pids"]["doi"]["identifier"],
                parent.get("id"),
                (parent.get("pids") or {}).get("doi", {}).get("identifier"),
                tombstone.get("note"),
                removal_reason,
                tombstone.get("removal_date"),
                tombstone.get("citation_text") if removal_reason != "spam" else None,
            ]
        except Exception:
            current_app.logger.exception(
                "Could not export deleted record: %s", record_id
            )
            return 1

        deleted_writer.writerow(row)
        return 0

    errors = 0
    for format in formats:
        try:
            content = SERIALIZERS[format](record)
        except Exception:
            current_app.logger.exception(
                "Could not serialize record %s as %s", record_id, format
            )
            errors += 1
            continue

        info = tarfile.TarInfo(f"{record_id}.{format}")
        info.size = len(content)
        archives[format].addfile(info, fileobj=BytesIO(content))

    return errors
