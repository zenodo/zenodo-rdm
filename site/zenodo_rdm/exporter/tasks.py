# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter tasks."""

import gzip
import io
import json
from datetime import datetime

from celery import shared_task
from flask import current_app
from invenio_app.factory import create_api
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_files_rest.models import Bucket, Location, ObjectVersion, as_bucket
from invenio_search.proxies import current_search_client as client
from opensearch_dsl import Search

from zenodo_rdm.exporter.config import (
    EXPORTER_BUCKET_UUID,
    EXPORTER_NUMBER_VERSIONS_TO_KEEP,
)


def _dump_records(community_slug):

    community_uuid = (
        db.session.query(CommunityMetadata.id)
        .filter(CommunityMetadata.slug == community_slug)
        .scalar()
    )

    app = create_api()

    with app.app_context():
        idxprefix = current_app.config["SEARCH_INDEX_PREFIX"]

        # Dump the records
        t1 = datetime.now()
        print("Writing records ...")
        query = f"is_published:true AND is_deleted:false AND parent.communities.ids:{community_uuid}"
        s = (
            Search(using=client, index=f"{idxprefix}rdmrecords-records")
            .extra(
                track_total_hits=True,
            )
            .query(
                "query_string",
                query=query,
            )
        )

        stream = io.StringIO()

        i = 0
        for r in s.scan():
            stream.write(json.dumps(r._d_))
            i += 1
            if i % 1000 == 0:
                print("...", i)
        print(f"... wrote {i} records")

        t2 = datetime.now()
        print("Writing records", t2 - t1)

        stream.seek(0)

        return stream


def _create_or_get_bucket():
    bucket = as_bucket(EXPORTER_BUCKET_UUID)
    if not bucket:
        print(f"Creating exporter bucket: {EXPORTER_BUCKET_UUID}")
        with db.session.begin_nested():
            # TODO: Set `quota_size` and `max_file_size`.
            bucket = Bucket(
                id=EXPORTER_BUCKET_UUID,
                default_location=Location.get_default().id,
                default_storage_class=current_app.config[
                    "FILES_REST_DEFAULT_STORAGE_CLASS"
                ],
            )
            db.session.add(bucket)
            db.session.commit()  # TODO: Commit here OK?
    else:
        print(f"Exporter bucket found: {EXPORTER_BUCKET_UUID}")
    return bucket


def _create_object_version(bucket, filename, stream, mimetype):
    # TODO: Should we pass in `size` to `set_contents` since we know the size of the stream?
    object_version = ObjectVersion.create(
        bucket=bucket, key=filename, stream=stream, mimetype=mimetype
    )
    print(f"Creating object version: {object_version}")
    db.session.add(object_version)
    db.session.commit()  # TODO: Commit here OK?


def _remove_old_object_versions(bucket, filename):
    all_object_versions = ObjectVersion.get_versions(
        bucket=bucket, key=filename, desc=True
    )
    for old_object_version in all_object_versions[EXPORTER_NUMBER_VERSIONS_TO_KEEP:]:
        print(f"Removing pervious object version: {old_object_version}")
        # Using `remove` (and not `delete`) since we really want to free up space.
        old_object_version.remove()
    db.session.commit()  # TODO: Commit here OK?


@shared_task
def export_community_records(community_slug):
    """Export community records."""

    bucket = _create_or_get_bucket()

    filename = f"{community_slug}/records.jsonl.gz"
    mimetype = "application/gzip"

    stream = _dump_records(community_slug)

    # TODO: Compress to GZIP in memory.
    bytes_stream = io.BytesIO(stream.read().encode())

    _create_object_version(bucket, filename, bytes_stream, mimetype)

    stream.close()

    _remove_old_object_versions(bucket, filename)
