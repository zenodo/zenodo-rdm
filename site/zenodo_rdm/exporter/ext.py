# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM exporter extension."""

from zenodo_rdm.exporter import config


class ZenodoExporter(object):
    """Zenodo exporter extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    @staticmethod
    def init_config(app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("EXPORTER_"):
                app.config.setdefault(k, getattr(config, k))

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["zenodo-exporter"] = self
