# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Sitemap generation for ZenodoRDM."""

from invenio_cache import current_cache

from zenodo_rdm.sitemap import config
from zenodo_rdm.sitemap.generators import generator_fns


class ZenodoSitemap(object):
    """Zenodo sitemap extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        self.init_config(app)
        self.generators = [fn for fn in generator_fns]
        app.extensions["zenodo-sitemap"] = self
        # Keep the currently stored sitemap cache keys for easy clearing
        self.cache_keys = set()

    def set_cache(self, key, value):
        """Set the sitemap cache."""
        current_cache.set(key, value, timeout=-1)
        self.cache_keys.add(key)

    @staticmethod
    def get_cache(key):
        """Get the sitemap cache."""
        current_cache.get(key)

    def clear_cache(self):
        """Clear the sitemap cache."""
        for key in self.cache_keys:
            current_cache.delete(key)
        self.cache_keys = set()

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("ZENODO_SITEMAP_"):
                app.config.setdefault(k, getattr(config, k))

    def _generate_all_urls(self):
        """Run all generators and yield the sitemap JSON entries."""
        for generator in self.generators:
            for generated in generator():
                yield generated
