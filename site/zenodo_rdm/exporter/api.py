# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Export records."""

from pathlib import Path
from tempfile import TemporaryDirectory

from flask import current_app
from invenio_db import db
from invenio_files_rest.models import Bucket, Location, ObjectVersion

from zenodo_rdm.exporter.readers import read_records
from zenodo_rdm.exporter.writers import EXPORT_FORMATS, write_archives

EXPORT_MIMETYPE = "application/gzip"


def export_records(formats, community_slug):
    """Export records to the configured bucket."""
    # Validate the request
    formats = tuple(formats)
    if not formats:
        raise ValueError("At least one export format is required")
    if len(formats) != len(set(formats)):
        raise ValueError("Duplicate export formats are not allowed")

    unsupported = set(formats) - set(EXPORT_FORMATS)
    if unsupported:
        raise ValueError(f"Unsupported formats: {', '.join(sorted(unsupported))}")

    # Prepare the staging directory
    configured_path = current_app.config["EXPORTER_STAGING_PATH"]
    staging_path = Path(
        configured_path or Path(current_app.instance_path) / "archive/exporter"
    )
    staging_path.mkdir(parents=True, exist_ok=True)

    with TemporaryDirectory(dir=staging_path) as run_path:
        # Read records once and write every requested format
        record_stream = read_records(community_slug)
        paths = write_archives(Path(run_path), formats, record_stream)

        prefix = f"{community_slug}/" if community_slug else ""
        files = [(path, f"{prefix}{path.name}") for path in paths]

        # Prepare the final bucket after the files are complete
        bucket_id = current_app.config["EXPORTER_BUCKET_UUID"]
        bucket = Bucket.get(bucket_id)
        if bucket:
            current_app.logger.info(f"Exporter bucket found: {bucket_id}")
        else:
            current_app.logger.info(f"Creating exporter bucket: {bucket_id}")
            bucket = Bucket(
                id=bucket_id,
                default_location=Location.get_default().id,
                default_storage_class=current_app.config[
                    "FILES_REST_DEFAULT_STORAGE_CLASS"
                ],
            )
            db.session.add(bucket)
            db.session.commit()
            # SQLAlchemy applies the configured defaults when these are None
            # during the first flush
            bucket.quota_size = None
            bucket.max_file_size = None
            db.session.commit()

        # Store each file as a new object version
        for path, key in files:
            try:
                version = ObjectVersion.create(
                    bucket=bucket,
                    key=key,
                    mimetype=EXPORT_MIMETYPE,
                )
                current_app.logger.info(f"Creating object version: {version}")
                with path.open("rb") as stream:
                    version.set_contents(stream, size=path.stat().st_size)
                db.session.add(version)
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

        # Remove versions beyond the configured retention count
        keep = current_app.config["EXPORTER_NUMBER_VERSIONS_TO_KEEP"]
        for _, key in files:
            try:
                versions = ObjectVersion.get_versions(
                    bucket=bucket,
                    key=key,
                    desc=True,
                )
                for version in versions[keep:]:
                    current_app.logger.info(
                        f"Removing previous object version: {version}"
                    )
                    version.remove()
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
