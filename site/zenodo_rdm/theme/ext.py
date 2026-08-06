# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM Theme module."""

from invenio_administration.permissions import administration_permission


class ZenodoTheme:
    """Zenodo Theme extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions["zenodo-theme"] = self
        app.jinja_env.globals["is_admin"] = administration_permission.can
