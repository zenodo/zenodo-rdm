# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tasks for metrics."""

from celery import shared_task

from zenodo_rdm.metrics import utils


@shared_task(ignore_result=True)
def calculate_metrics(metric_id=None):
    """Calculate metrics for the passed metric ID."""
    utils.calculate_metrics(metric_id)
