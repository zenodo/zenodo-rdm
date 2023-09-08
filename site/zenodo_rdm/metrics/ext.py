# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoMetrics module."""

from __future__ import absolute_import, print_function

from flask import current_app

from . import config


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
            if k.startswith('ZENODO_METRICS'):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['zenodo-metrics'] = self

    @property
    def metrics_start_date(self):
        """Get get metrics start date from config."""
        return current_app.config['ZENODO_METRICS_START_DATE']
