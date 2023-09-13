# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Utilities for metrics module."""
from copy import deepcopy

from flask import current_app
from invenio_cache import current_cache


def get_metrics(metric_id):
    cached_data = current_cache.get(f"METRICS_CACHE::{metric_id}")
    if cached_data is not None:
        return cached_data


def calculate_metrics(metric_id, cache=True):
    """Calculate a metric's result."""
    result = deepcopy(current_app.config["METRICS_DATA"][metric_id])

    for metric in result:
        metric["value"] = metric["value"]()

    if cache:
        current_cache.set(
            f"METRICS_CACHE::{metric_id}",
            result,
            timeout=current_app.config["METRICS_CACHE_TIMEOUT"],
        )

    return result


def formatted_response(metrics):
    """Format metrics into Prometheus format."""
    response = ""
    for metric in metrics:
        response += (
            "# HELP {name} {help}\n# TYPE {name} {type}\n{name} "
            "{value}\n".format(**metric)
        )

    return response
