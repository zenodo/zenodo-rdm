# -*- coding: utf-8 -*-
#
# Copyright (C) 2023-2026 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo stats extension."""

import copy

from flask import current_app
from invenio_search.engine import SearchEngine
from werkzeug.utils import cached_property

from zenodo_rdm.stats import config


class ZenodoStats(object):
    """Zenodo stats extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @cached_property
    def search_client(self):
        """Search client with stats-specific configuration."""
        client_config = current_app.config.get("STATS_SEARCH_CLIENT_CONFIG") or {}
        hosts = current_app.config.get("STATS_SEARCH_HOSTS")
        host_opts = current_app.config.get("STATS_SEARCH_HOST_CONNECTION_OPTIONS")
        if hosts is None:
            hosts = current_app.config.get("SEARCH_HOSTS")
        if host_opts and hosts:
            hosts = [
                {**h, **host_opts} if isinstance(h, dict) else h
                for h in copy.deepcopy(hosts)
            ]
        client_config.setdefault("hosts", hosts)
        return SearchEngine(**client_config)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("STATS_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-stats"] = self
