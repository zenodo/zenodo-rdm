# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Proxy objects for easier access to application objects."""

from flask import current_app
from werkzeug.local import LocalProxy

current_moderation = LocalProxy(lambda: current_app.extensions["zenodo-moderation"])
current_domain_tree = LocalProxy(lambda: current_moderation.domain_tree)
current_scores = LocalProxy(lambda: current_moderation.scores)
