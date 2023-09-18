# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE extension."""

from collections import defaultdict

from werkzeug.utils import cached_property

from . import config


class OpenAIREState(object):
    """Store the OpenAIRE mappings."""

    def __init__(self, app):
        """Constructor."""
        self.app = app

    @cached_property
    def openaire_communities(self):
        """Configuration for OpenAIRE communities types."""
        return self.app.config["OPENAIRE_COMMUNITIES"]

    @cached_property
    def inverse_openaire_community_map(self):
        """Lookup for Zenodo community -> OpenAIRE community."""
        comm_map = self.openaire_communities
        items = defaultdict(list)
        for oa_comm, cfg in comm_map.items():
            for z_comm in cfg["communities"]:
                items[z_comm].append(oa_comm)
        return items


class OpenAIRE(object):
    """Zenodo OpenAIRE extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("OPENAIRE_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.state = OpenAIREState(app)
        app.extensions["invenio-openaire"] = self
