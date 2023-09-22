# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM module that adds support for prometheus metrics."""

import humanize
from flask import Blueprint, Response, current_app
from invenio_cache import current_cache

from zenodo_rdm.metrics import tasks, utils

blueprint = Blueprint("METRICS", __name__)


@blueprint.route("/metrics/<string:metric_id>")
def metrics(metric_id):
    """Metrics endpoint."""
    if metric_id not in current_app.config["METRICS_DATA"]:
        return Response("Invalid key", status=404, mimetype="text/plain")

    metrics = utils.get_metrics(metric_id)
    if metrics:
        response = utils.formatted_response(metrics)
        return Response(response, mimetype="text/plain")

    # Send off task to compute metrics only if it wasn't already requested
    if not current_cache.get(f"METRICS_EVALUATING::{metric_id}"):
        tasks.calculate_metrics.delay(metric_id)
        current_cache.set(f"METRICS_EVALUATING::{metric_id}", True, timeout=60 * 2)

    retry_after = current_app.config["METRICS_CACHE_UPDATE_INTERVAL"]
    return Response(
        f"Metrics not available. Try again after {humanize.naturaldelta(retry_after)}.",
        status=503,
        headers={"Retry-After": int(retry_after.total_seconds())},
    )
