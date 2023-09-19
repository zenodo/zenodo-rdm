# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tasks for statistics."""

from celery import shared_task
from dateutil.parser import parse as dateutil_parse
from flask import current_app

from zenodo_rdm.stats.exporters import PiwikExporter


@shared_task(ignore_result=True, max_retries=3, default_retry_delay=60 * 60)
def export_stats(start_date=None, end_date=None, update_bookmark=True, retry=False):
    """Export stats events."""
    if current_app.config["STATS_PIWIK_EXPORT_ENABLED"] is True:
        start_date = dateutil_parse(start_date) if start_date else None
        end_date = dateutil_parse(end_date) if end_date else None

        try:
            PiwikExporter().run(
                start_date=start_date,
                end_date=end_date,
                update_bookmark=update_bookmark,
            )
        except Exception as exc:
            if retry:
                export_stats.retry(exc=exc)
