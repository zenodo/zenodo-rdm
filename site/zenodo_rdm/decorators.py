# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Decorators."""


from functools import wraps

from invenio_cache import current_cache
from flask import session
from flask_login import current_user


def has_flashes_or_authenticated_user():
    """Return True if there are pending flashes or user is authenticated."""
    return "_flashes" in session or current_user.is_authenticated


def cached_unless_authenticated_or_flashes(timeout=50, key_prefix="default"):
    """Cache anonymous traffic."""
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cache_fun = current_cache.cached(
                timeout=timeout, key_prefix=key_prefix,
                unless=has_flashes_or_authenticated_user)
            return cache_fun(f)(*args, **kwargs)
        return wrapper
    return caching
