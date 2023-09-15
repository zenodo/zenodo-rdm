# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Proxies for ZenodoRDM stats module."""

from __future__ import absolute_import, print_function

from flask import current_app
from werkzeug.local import LocalProxy

current_stats_search_client = LocalProxy(
    lambda: current_app.extensions["zenodo-stats"].search_client
)
"""Proxy to Elasticsearch client used for statistics queries."""
