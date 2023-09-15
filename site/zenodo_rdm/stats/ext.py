# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Exporter extension."""

from __future__ import absolute_import, print_function

from elasticsearch import Elasticsearch
from elasticsearch.connection import RequestsHttpConnection
from flask import current_app
from werkzeug.utils import cached_property

from . import config


class ZenodoStats(object):
    """Zenodo stats extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @cached_property
    def search_client(self):
        """Elasticsearch client for stats queries."""
        client_config = (
            current_app.config.get("ZENODO_STATS_ELASTICSEARCH_CLIENT_CONFIG") or {}
        )
        client_config.setdefault(
            "hosts", current_app.config.get("SEARCH_ELASTIC_HOSTS")
        )
        client_config.setdefault("connection_class", RequestsHttpConnection)
        return Elasticsearch(**client_config)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("ZENODO_STATS_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-stats"] = self
