# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM Metrics module."""

from flask import current_app

from zenodo_rdm.metrics import config


class ZenodoMetrics(object):
    """Zenodo frontpage extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("METRICS"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-metrics"] = self

    @property
    def metrics_start_date(self):
        """Get get metrics start date from config."""
        return current_app.config["METRICS_START_DATE"]
