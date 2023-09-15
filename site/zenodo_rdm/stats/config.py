# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Configuration for ZenodoRDM stats."""

ZENODO_STATS_PIWIK_EXPORTER = {
    "id_site": 1,
    "url": "https://analytics.openaire.eu/piwik.php",
    "token_auth": "api-token",
    "chunk_size": 50,  # [max piwik payload size = 64k] / [max querystring size = 750]
}

ZENODO_STATS_PIWIK_EXPORT_ENABLED = True

# Queries performed when processing aggregations might take more time than
# usual. This is fine though, since this is happening during Celery tasks.
ZENODO_STATS_ELASTICSEARCH_CLIENT_CONFIG = {"timeout": 60}
