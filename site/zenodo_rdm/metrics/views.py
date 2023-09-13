# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM module that adds support for prometheus metrics."""

import humanize
from flask import Blueprint, Response, current_app

from . import tasks, utils

blueprint = Blueprint("zenodo_metrics", __name__)


@blueprint.route("/metrics/<string:metric_id>")
def metrics(metric_id):
    """Metrics endpoint."""
    if metric_id not in current_app.config["ZENODO_METRICS_DATA"]:
        return Response("Invalid key", status=404, mimetype="text/plain")

    metrics = utils.get_metrics(metric_id)
    if metrics:
        response = utils.formatted_response(metrics)
        return Response(response, mimetype="text/plain")

    # Send off task to compute metrics
    tasks.calculate_metrics.delay(metric_id)
    retry_after = current_app.config["ZENODO_METRICS_CACHE_UPDATE_INTERVAL"]
    return Response(
        "Metrics not available. Try again after {}.".format(
            humanize.naturaldelta(retry_after)
        ),
        status=503,
        headers={"Retry-After": int(retry_after.total_seconds())},
    )
