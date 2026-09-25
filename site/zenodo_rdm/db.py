#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Database helpers."""

from flask import current_app, request
from flask_login import current_user


def routed_bind(session, *args, **kwargs):
    """Route session to the appropriate database depending on the request context.

    Routes unauthenticated/anonymous GET and HEAD requests of configured endpoints to
    the configured read replica SQLAlchemy bind.

    Falls back to the primary database (by returning ``None``) when outside a
    request/app context, for non-read HTTP methods, for authenticated users, for
    endpoints not listed in ``ZENODO_READ_REPLICA_ENDPOINTS``, or when the read
    replica bind is not configured.
    """
    if not current_app or not request:
        return None

    if request.method not in ["GET", "HEAD"]:
        return None
    read_endpoints = current_app.config.get("ZENODO_READ_REPLICA_ENDPOINTS", [])
    if request.endpoint not in read_endpoints:
        return None
    if not current_user.is_anonymous:
        return None

    return session._db.engines.get("read_replica")
