# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM Metrics API."""

from __future__ import absolute_import

import calendar
from datetime import datetime, timedelta

import requests
from flask import current_app
from invenio_accounts.models import User
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_files_rest.models import FileInstance
from invenio_search import current_search_client
from invenio_search.utils import build_alias_name
from opensearchpy import Search

from .proxies import current_metrics


class ZenodoMetric(object):
    """API class for Zenodo Metrics."""

    @staticmethod
    def get_data_transfer():
        """Get file transfer volume in TB."""
        time_range = {"gte": current_metrics.metrics_start_date.isoformat()}

        search = (
            Search(
                using=current_search_client,
                index=build_alias_name("stats-file-download"),
            )
            .filter(
                "range",
                timestamp=time_range,
            )
            .filter(
                "term",
                is_parent=False,
            )
            .params(request_timeout=120)
        )
        search.aggs.metric("download_volume", "sum", field="volume")
        result = search[:0].execute().aggregations.to_dict()
        download_volume = result.get("download_volume", {}).get("value", 0)

        search = (
            Search(using=current_search_client, index=build_alias_name("rdmrecords"))
            .filter("range", created=time_range)
            .params(request_timeout=120)
        )
        search.aggs.metric("upload_volume", "sum", field="files.totalbytes")
        result = search[:0].execute().aggregations.to_dict()
        upload_volume = result.get("upload_volume", {}).get("value", 0)

        return int(download_volume + upload_volume)

    @staticmethod
    def get_visitors():
        """Get number of unique zenodo users."""
        time_range = {"gte": current_metrics.metrics_start_date.isoformat()}

        search = (
            Search(
                using=current_search_client, index=build_alias_name("events-stats-*")
            )
            .filter("range", timestamp=time_range)
            .params(request_timeout=120)
        )

        search.aggs.metric("visitors_count", "cardinality", field="visitor_id")
        result = search[:0].execute()

        if "visitors_count" not in result.aggregations:
            return 0

        return int(result.aggregations.visitors_count.value)

    @staticmethod
    def get_uptime():
        """Get Zenodo uptime."""
        metrics = current_app.config["ZENODO_METRICS_UPTIME_ROBOT_METRIC_IDS"]
        url = current_app.config["ZENODO_METRICS_UPTIME_ROBOT_URL"]
        api_key = current_app.config["ZENODO_METRICS_UPTIME_ROBOT_API_KEY"]

        end = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        start = (end - timedelta(days=1)).replace(day=1)
        end_ts = calendar.timegm(end.utctimetuple())
        start_ts = calendar.timegm(start.utctimetuple())

        res = requests.post(
            url,
            json={
                "api_key": api_key,
                "custom_uptime_ranges": f"{start_ts}_{end_ts}",
            },
        )

        return sum(
            float(d["custom_uptime_ranges"])
            for d in res.json()["monitors"]
            if d["id"] in metrics
        ) / len(metrics)

    @staticmethod
    def get_researchers():
        """Get number of unique zenodo users."""
        return User.query.filter(
            User.confirmed_at.isnot(None),
            User.active.is_(True),
        ).count()

    @staticmethod
    def get_files():
        """Get number of files."""
        return FileInstance.query.count()

    @staticmethod
    def get_communities():
        """Get number of active communities."""
        return CommunityMetadata.query.filter(
            CommunityMetadata.is_deleted.is_(False)
        ).count()
