# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenAIRE proxies."""

from flask import current_app
from werkzeug.local import LocalProxy

current_openaire = LocalProxy(lambda: current_app.extensions["invenio-openaire"])
