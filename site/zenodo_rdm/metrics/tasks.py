# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tasks for metrics."""

from celery import shared_task

from . import utils


@shared_task(ignore_result=True)
def calculate_metrics(metric_id=None):
    """Calculate metrics for the passed metric ID."""
    utils.calculate_metrics(metric_id)
