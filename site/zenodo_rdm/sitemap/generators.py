# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Sitemap generators."""

import arrow
from flask import current_app, url_for
from invenio_communities.models import Community
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
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
        db.session.query(PersistentIdentifier, RecordMetadata)
        .join(RecordMetadata, RecordMetadata.id == PersistentIdentifier.object_uuid)
        .filter(
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_type == "recid",
        )
    )

    scheme = current_app.config["ZENODO_SITEMAP_URL_SCHEME"]
    for pid, rm in q.yield_per(1000):
        yield {
            "loc": url_for(
                "invenio_records_ui.recid",
                pid_value=pid.pid_value,
                _external=True,
                _scheme=scheme,
            ),
            "lastmod": _sitemapdtformat(rm.updated),
        }


def communities_generator():
    """Generate the communities links."""
    q = Community.query.filter(Community.deleted_at.is_(None))
    scheme = current_app.config["ZENODO_SITEMAP_URL_SCHEME"]
    for comm in q.yield_per(1000):
        for endpoint in "detail", "search", "about":
            yield {
                "loc": url_for(
                    "invenio_communities.{}".format(endpoint),
                    community_id=comm.id,
                    _external=True,
                    _scheme=scheme,
                ),
                "lastmod": _sitemapdtformat(comm.updated),
            }


generator_fns = [
    records_generator,
    communities_generator,
]
