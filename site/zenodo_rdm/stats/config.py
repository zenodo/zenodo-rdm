# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Configuration for ZenodoRDM stats."""

STATS_PIWIK_EXPORTER = {
    "id_site": 1,
    "url": "https://analytics.openaire.eu/piwik.php",
    "token_auth": "api-token",
    "chunk_size": 50,  # [max piwik payload size = 64k] / [max querystring size = 750]
}

STATS_PIWIK_EXPORT_ENABLED = False
