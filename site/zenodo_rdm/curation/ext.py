# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM Curation module."""

from flask import current_app
from werkzeug.utils import cached_property

from . import config


class ZenodoCuration:
    """Zenodo content curation extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("CURATION_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-curation"] = self

    @cached_property
    def scores(self):
        """Return curation scores used for rules."""
        return {
            **config.CURATION_SCORES,
            **current_app.config.get("CURATION_SCORES", {}),
        }

    @cached_property
    def thresholds(self):
        """Return curation thresholds used for rules/curators."""
        return {
            **config.CURATION_THRESHOLDS,
            **current_app.config.get("CURATION_THRESHOLDS", {}),
        }
