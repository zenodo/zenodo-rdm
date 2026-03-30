# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Proxy objects for easier access to application objects."""

from flask import current_app
from werkzeug.local import LocalProxy

current_moderation = LocalProxy(lambda: current_app.extensions["zenodo-moderation"])
current_scores = LocalProxy(lambda: current_moderation.scores)
