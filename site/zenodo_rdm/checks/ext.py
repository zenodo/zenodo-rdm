# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM Checks module."""

from invenio_administration.permissions import administration_permission


class ZenodoChecks:
    """Zenodo checks extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions["zenodo-checks"] = self
        app.jinja_env.globals["administration_permission"] = administration_permission