# -*- coding: utf-8 -*-
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
    """
    if request and request.method in ["GET", "HEAD"]:
        read_endpoints = current_app.config.get("ZENODO_READ_REPLICA_ENDPOINTS", [])
        if current_user.is_anonymous and request.endpoint in read_endpoints:
            return session._db.engines["read_replica"]
