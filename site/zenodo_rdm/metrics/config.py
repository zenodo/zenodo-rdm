# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Configuration for ZenodoRDM Metrics."""

import datetime

from .api import ZenodoMetric

ZENODO_METRICS_START_DATE = datetime.datetime(2021, 1, 1)
ZENODO_METRICS_CACHE_TIMEOUT = int(datetime.timedelta(hours=1).total_seconds())
ZENODO_METRICS_CACHE_UPDATE_INTERVAL = datetime.timedelta(minutes=30)

ZENODO_METRICS_UPTIME_ROBOT_METRIC_IDS = {}
ZENODO_METRICS_UPTIME_ROBOT_URL = "https://api.uptimerobot.com/v2/getMonitors"
ZENODO_METRICS_UPTIME_ROBOT_API_KEY = None

ZENODO_METRICS_DATA = {
    "openaire-nexus": [
        {
            "name": "zenodo_nexus_data_transfer_bytes_total",
            "help": (
                "Bytes of data transferred from/to Zenodo during the "
                "OpenAIRE-NEXUS project (i.e. from 2021-01-01)."
            ),
            "type": "counter",
            "value": ZenodoMetric.get_data_transfer,
        },
        {
            "name": "zenodo_nexus_unique_visitors_web_total",
            "help": (
                "Total of daily unique visitors on Zenodo portal during the "
                "OpenAIRE-NEXUS project (i.e. from 2021-01-01)."
            ),
            "type": "counter",
            "value": ZenodoMetric.get_visitors,
        },
        {
            "name": "zenodo_last_month_uptime_ratio",
            "help": "Zenodo uptime percentage for the last month.",
            "type": "gauge",
            "value": ZenodoMetric.get_uptime,
        },
        {
            "name": "zenodo_researchers",
            "help": "Number of researchers registered on Zenodo",
            "type": "gauge",
            "value": ZenodoMetric.get_researchers,
        },
        {
            "name": "zenodo_files",
            "help": "Number of files hosted on Zenodo",
            "type": "gauge",
            "value": ZenodoMetric.get_files,
        },
        {
            "name": "zenodo_communities",
            "help": "Number of Zenodo communities created",
            "type": "gauge",
            "value": ZenodoMetric.get_communities,
        },
    ]
}
