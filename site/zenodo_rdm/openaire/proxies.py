# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE proxies."""

from flask import current_app
from werkzeug.local import LocalProxy

current_openaire = LocalProxy(lambda: current_app.extensions["invenio-openaire"])
