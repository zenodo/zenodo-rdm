# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM exporter tasks."""

import csv
import gzip
import json
import tarfile
import time
from io import BytesIO, TextIOWrapper

from celery import shared_task
from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from invenio_access.permissions import any_user
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_files_rest.models import Bucket, Location, ObjectVersion, as_bucket
from invenio_rdm_records.oai import oai_datacite_etree
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_search import current_search_client
from lxml import etree

from zenodo_rdm.exporter.pit import pit_scan

RECORDS_MIMETYPE = "application/gzip"
DELETED_MIMETYPE = "application/gzip"

# Progress logging: whichever threshold fires first. Tuned for multi-day runs
# on ~6M records — caps log volume while still surfacing stalls within minutes.
PROGRESS_LOG_EVERY_RECORDS = 10_000
PROGRESS_LOG_EVERY_SECONDS = 300


def _fmt_duration(seconds):
    """Format seconds as ``H:MM:SS`` or ``Nd HH:MM:SS`` for multi-day runs."""
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours}:{minutes:02d}:{secs:02d}"


def _get_anonymous_identity():
    anonymous_identity = AnonymousIdentity()
    with current_app.test_request_context():
        identity_changed.send(current_app, identity=anonymous_identity)
        anonymous_identity.provides.add(any_user)
    return anonymous_identity


def _scan_records(identity, community_uuid, use_pit, page_size=1000):
    """Return ``(result, total)`` where ``result.hits`` iterates all matches.

    Both paths return a total so callers can compute progress and ETA.
    PIT's total is the exact snapshot count; scroll's total comes from a
    separate ``count()`` request and may drift slightly vs the scroll
    snapshot during long runs, but the error is negligible on our scale.

    ``page_size`` controls records-per-batch for both paths.
    """
    params = {"allversions": True, "include_deleted": True}
    q = f"parent.communities.ids:{community_uuid}" if community_uuid else ""
    search = service._search("scan", identity, params, search_preference=None, q=q)

    if use_pit:
        hits = pit_scan(index=search._index, body=search.to_dict(), size=page_size)
        total = hits.total
    else:
        hits = search.params(size=page_size).scan()
        count_body = {"query": search.to_dict().get("query", {"match_all": {}})}
        total = current_search_client.count(
            index=search._index, body=count_body
        )["count"]

    result = service.result_list(
        service,
        identity,
        hits,
        params,
        links_tpl=None,
        links_item_tpl=service.links_item_tpl,
        expandable_fields=service.expandable_fields,
    )
    return result, total


def _log_progress(count, total, start, last_log, last_count):
    """Emit one progress line; return the new ``(last_log, last_count)``."""
    now = time.monotonic()
    elapsed = now - start
    avg_rate = count / elapsed if elapsed > 0 else 0
    window = now - last_log
    recent_rate = (count - last_count) / window if window > 0 else avg_rate
    pct = count * 100 / total if total else 0
    eta = (total - count) / recent_rate if total and recent_rate > 0 else 0

    current_app.logger.info(
        f"[exporter] {count:,}/{total:,} ({pct:.2f}%) | "
        f"rate={recent_rate:,.0f}/s avg={avg_rate:,.0f}/s | "
        f"ETA {_fmt_duration(eta)}"
    )
    return now, count


def _export_records_to_files(
    format,
    community_slug,
    records_file,
    deleted_file,
    use_pit=False,
    page_size=1000,
):
    community_uuid = None

    if community_slug:
        community_uuid = (
            db.session.query(CommunityMetadata.id)
            .filter(CommunityMetadata.slug == community_slug)
            .one()[0]
        )

    anonymous_identity = _get_anonymous_identity()

    res, total = _scan_records(
        anonymous_identity, community_uuid, use_pit, page_size=page_size
    )

    mode = "pit" if use_pit else "scroll"
    current_app.logger.info(
        f"[exporter] starting: format={format} "
        f"community={community_slug or '-'} mode={mode} "
        f"page_size={page_size} total={total:,}"
    )
    start = time.monotonic()
    last_log = start
    last_count = 0
    count = 0

    deleted_file_content = TextIOWrapper(deleted_file, encoding="utf-8")
    deleted_writer = csv.writer(deleted_file_content)
    deleted_writer.writerow(
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
    )

    for idx, record in enumerate(res.hits):
        record_id = record.get("id")
        if not record_id:
            continue

        is_deleted = record.get("deletion_status", {}).get("is_deleted", False)
        if is_deleted:
            removal_reason = (
                record.get("tombstone", {}).get("removal_reason", {}).get("id")
            )
            deleted_writer.writerow(
                [
                    record_id,
                    record["pids"]["doi"]["identifier"],
                    record.get("parent", {}).get("id"),
                    record.get("parent", {})
                    .get("pids", {})
                    .get("doi", {})
                    .get("identifier"),
                    record.get("tombstone", {}).get("note"),
                    removal_reason,
                    record.get("tombstone", {}).get("removal_date"),
                    (
                        record.get("tombstone", {}).get("citation_text")
                        if removal_reason != "spam"
                        else None
                    ),
                ]
            )
            continue

        if format == "json":
            content_bytes = json.dumps(record).encode()
        elif format == "xml":
            try:
                oai_etree = oai_datacite_etree(None, {"_source": record})
                content_bytes = etree.tostring(
                    oai_etree,
                    xml_declaration=True,
                    encoding="UTF-8",
                )
            except Exception as e:
                current_app.logger.exception(f"Error serializing {record_id}: {e}")
        else:
            raise ValueError(f"Unsupported format '{format}'")

        filename = f"{record_id}.{format}"
        tar_info = tarfile.TarInfo(filename)
        file_content = BytesIO()
        file_content.name = filename
        file_content.write(content_bytes)
        file_content.seek(0)
        tar_info.size = len(content_bytes)
        records_file.addfile(tar_info, fileobj=file_content)

        count = idx + 1
        if (
            count - last_count >= PROGRESS_LOG_EVERY_RECORDS
            or time.monotonic() - last_log >= PROGRESS_LOG_EVERY_SECONDS
        ):
            last_log, last_count = _log_progress(
                count, total, start, last_log, last_count
            )

    elapsed = time.monotonic() - start
    avg = count / elapsed if elapsed > 0 else 0
    current_app.logger.info(
        f"[exporter] done: {count:,} records in {_fmt_duration(elapsed)} "
        f"(avg {avg:,.0f}/s)"
    )


def _create_or_get_bucket():
    bucket_uuid = current_app.config["EXPORTER_BUCKET_UUID"]
    bucket = as_bucket(bucket_uuid)
    if not bucket:
        current_app.logger.info(f"Creating exporter bucket: {bucket_uuid}")
        bucket = Bucket(
            id=bucket_uuid,
            default_location=Location.get_default().id,
            default_storage_class=current_app.config[
                "FILES_REST_DEFAULT_STORAGE_CLASS"
            ],
        )
        db.session.add(bucket)
        db.session.commit()
        # Revert default values coming from the config.
        bucket.quota_size = None
        bucket.max_file_size = None
        db.session.commit()
    else:
        current_app.logger.info(f"Exporter bucket found: {bucket_uuid}")
    return bucket


def _create_object_version(bucket, file_stream, filename, mimetype):
    object_version = ObjectVersion.create(
        bucket=bucket, key=filename, mimetype=mimetype
    )
    current_app.logger.info(f"Creating object version: {object_version}")
    object_version.set_contents(file_stream)
    db.session.add(object_version)
    db.session.commit()


def _remove_old_object_versions(bucket, filename):
    number_versions_to_keep = current_app.config["EXPORTER_NUMBER_VERSIONS_TO_KEEP"]
    object_versions = ObjectVersion.get_versions(bucket=bucket, key=filename, desc=True)
    for object_version in object_versions[number_versions_to_keep:]:
        current_app.logger.info(f"Removing previous object version: {object_version}")
        # Using `remove` (and not `delete`) since we really want to free up space.
        object_version.remove()
    db.session.commit()


@shared_task
def export_records(format, community_slug, use_pit=False, page_size=1000):
    """Export records."""
    bucket = _create_or_get_bucket()

    records_file_stream = BytesIO()
    deleted_file_stream = BytesIO()

    with (
        tarfile.open(fileobj=records_file_stream, mode="w|gz") as records_file,
        gzip.GzipFile(fileobj=deleted_file_stream, mode="w") as deleted_file,
    ):
        _export_records_to_files(
            format,
            community_slug,
            records_file,
            deleted_file,
            use_pit=use_pit,
            page_size=page_size,
        )

    records_file_stream.seek(0)
    deleted_file_stream.seek(0)

    filename_prefix = f"{community_slug}/" if community_slug else ""
    records_filename = f"{filename_prefix}records-{format}.tar.gz"
    deleted_filename = f"{filename_prefix}records-deleted.csv.gz"

    _create_object_version(
        bucket, records_file_stream, records_filename, RECORDS_MIMETYPE
    )
    _create_object_version(
        bucket, deleted_file_stream, deleted_filename, DELETED_MIMETYPE
    )

    _remove_old_object_versions(bucket, records_filename)
    _remove_old_object_versions(bucket, deleted_filename)
