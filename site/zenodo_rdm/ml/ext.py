# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM machine learning module."""

from flask import current_app

from . import config


class ZenodoML:
    """Zenodo machine learning extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("ML_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-ml"] = self

    def _parse_model_name_version(self, model):
        """Parse model name and  version."""
        vals = model.rsplit(":")
        version = vals[1] if len(vals) > 1 else None
        return vals[0], version

    def models(self, model, **kwargs):
        """Return model based on model name."""
        models = current_app.config.get("ML_MODELS", {})
        model_name, version = self._parse_model_name_version(model)

        if model_name not in models:
            raise ValueError("Model not found/registered.")

        return models[model_name](version=version, **kwargs)
