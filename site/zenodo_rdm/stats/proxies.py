# SPDX-FileCopyrightText: 2023-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Proxies for ZenodoRDM stats."""

from flask import current_app
from werkzeug.local import LocalProxy

current_stats_search_client = LocalProxy(
    lambda: current_app.extensions["zenodo-stats"].search_client
)
