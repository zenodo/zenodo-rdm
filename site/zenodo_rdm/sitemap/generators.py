# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Sitemap generators."""

import arrow
from flask import current_app, url_for
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_rdm_records.records.models import RDMRecordMetadata
from invenio_records.models import RecordMetadata


def _sitemapdtformat(dt):
    """Convert a datetime to a W3 Date and Time format.

    Converts the date to a minute-resolution datetime timestamp with a special
    UTC designator 'Z'. See more information at
    https://www.w3.org/TR/NOTE-datetime.
    """
    adt = arrow.Arrow.fromdatetime(dt).to("utc")
    return adt.format("YYYY-MM-DDTHH:mm:ss") + "Z"


def records_generator():
    """Generate the records links."""
    q = (
        db.session.query(PersistentIdentifier.pid_value, RDMRecordMetadata.updated)
        .join(
            RDMRecordMetadata, RDMRecordMetadata.id == PersistentIdentifier.object_uuid
        )
        .filter(
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_type == "recid",
            RDMRecordMetadata.deletion_status == "P",
        )
    )

    scheme = current_app.config["SITEMAP_URL_SCHEME"]
    for pid_value, updated_at in q.yield_per(1000):
        yield {
            "loc": url_for(
                "invenio_app_rdm_records.record_detail",
                pid_value=pid_value,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(updated_at),
        }


def communities_generator():
    """Generate the communities links."""
    q = db.session.query(CommunityMetadata.slug, CommunityMetadata.updated).filter(
        CommunityMetadata.deletion_status == "P"
    )
    scheme = current_app.config["SITEMAP_URL_SCHEME"]
    for comm_slug, updated_at in q.yield_per(1000):
        yield {
            "loc": url_for(
                "invenio_app_rdm_communities.communities_detail",
                pid_value=comm_slug,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(updated_at),
        }
        yield {
            "loc": url_for(
                "invenio_communities.communities_about",
                pid_value=comm_slug,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(updated_at),
        }


generator_fns = [
    records_generator,
    communities_generator,
]
