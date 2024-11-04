# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM Moderation module."""

from types import SimpleNamespace

from flask import current_app
from werkzeug.utils import cached_property

from . import config


class ZenodoModeration:
    """Zenodo content moderation extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("MODERATION_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-moderation"] = self

    @cached_property
    def scores(self):
        """Return moderation score values used in rules."""
        return SimpleNamespace(**current_app.config.get("MODERATION_SCORES", {}))
