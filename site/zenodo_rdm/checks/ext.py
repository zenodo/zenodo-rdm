# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM Checks module."""

from zenodo_rdm.checks.checks_diff import diff_comparison


class ZenodoChecks:
    """Zenodo Checks extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions["zenodo-checks"] = self
        app.jinja_env.filters["diff_comparison"] = diff_comparison
