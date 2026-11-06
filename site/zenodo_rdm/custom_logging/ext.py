# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM custom logging module."""

import logging

from zenodo_rdm.custom_logging.handlers import OpenSearchHandler

from . import config

CUSTOM_LOGGING_LEVEL = 1000


def custom(self, key, message, *args, **kws):
    """Log level custom method."""
    if not isinstance(message, dict):
        raise ValueError("Message should be a dict")
    if self.isEnabledFor(CUSTOM_LOGGING_LEVEL):
        message["key"] = key
        self._log(CUSTOM_LOGGING_LEVEL, message, args, **kws)


class ZenodoCustomLogging:
    """Zenodo custom logging extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("CUSTOM_LOGGING_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        logging.addLevelName(CUSTOM_LOGGING_LEVEL, "CUSTOM")
        logging.Logger.custom = custom
        handler = OpenSearchHandler()
        for h in app.logger.handlers:
            if isinstance(h, handler.__class__):
                break
        else:
            app.logger.addHandler(handler)
        self.init_config(app)
