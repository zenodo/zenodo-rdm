# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Decorators."""


from functools import wraps

from flask import current_app, session
from flask_login import current_user
from invenio_cache import current_cache


def has_flashes_or_authenticated_user_or_development():
    """Return True if there are pending flashes or user is authenticated or dev."""
    return "_flashes" in session or current_user.is_authenticated or current_app.debug


def cached_unless_authenticated_or_flashes(timeout=50, key_prefix="default"):
    """Cache anonymous traffic."""

    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # we compute the cache key based on the `Dockerfile.IMAGE_BUILD_TIMESTAMP`
            cache_prefix = (
                f"{key_prefix}_{current_app.config.get('IMAGE_BUILD_TIMESTAMP', '')}"
            )
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=cache_prefix,
                unless=has_flashes_or_authenticated_user_or_development,
            )
            return cache_fun(f)(*args, **kwargs)

        return wrapper

    return caching
