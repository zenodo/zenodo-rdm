# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter tasks."""

import csv
import gzip
import json
import tarfile
from datetime import datetime
from io import BytesIO, TextIOWrapper

from celery import shared_task
from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from invenio_access.permissions import any_user
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_files_rest.models import (
    Bucket,
    Location,
    ObjectVersion,
    as_bucket,
)
from invenio_rdm_records.oai import oai_datacite_etree
from invenio_rdm_records.proxies import current_rdm_records_service as service
from lxml import etree

RECORDS_MIMETYPE = "application/gzip"
DELETED_MIMETYPE = "application/gzip"


def _get_anonymous_identity():
    anonymous_identity = AnonymousIdentity()
    with current_app.test_request_context():
        identity_changed.send(current_app, identity=anonymous_identity)
        anonymous_identity.provides.add(any_user)
    return anonymous_identity


def _export_records_to_files(format, community_slug, records_file, deleted_file):

    community_uuid = None

    if community_slug:
        community_uuid = (
            db.session.query(CommunityMetadata.id)
            .filter(CommunityMetadata.slug == community_slug)
            .one()[0]
        )

    anonymous_identity = _get_anonymous_identity()

    res = service.scan(
        anonymous_identity,
        q=f"parent.communities.ids:{community_uuid}" if community_uuid else "",
        params={"allversions": True, "include_deleted": True},
    )

    deleted_file_content = TextIOWrapper(deleted_file, encoding="utf-8")
    deleted_writer = csv.writer(deleted_file_content)
    deleted_writer.writerow(
        [
            "record_id",
            "doi",
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
            deleted_writer.writerow(
                [
                    record_id,
                    record["pids"]["doi"]["identifier"],
                    record.get("tombstone", {}).get("removal_reason", {}).get("id"),
                    record.get("tombstone", {}).get("removal_date"),
                    record.get("tombstone", {}).get("citation_text"),
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
def export_records(format, community_slug):
    """Export records."""
    bucket = _create_or_get_bucket()

    records_file_stream = BytesIO()
    deleted_file_stream = BytesIO()

    with tarfile.open(
        fileobj=records_file_stream, mode="w|gz"
    ) as records_file, gzip.GzipFile(
        fileobj=deleted_file_stream, mode="w"
    ) as deleted_file:
        _export_records_to_files(format, community_slug, records_file, deleted_file)

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
