# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Configuration for ZenodoRDM stats."""

STATS_PIWIK_EXPORTER = {
    "id_site": 1,
    "url": "https://analytics.openaire.eu/piwik.php",
    "token_auth": "api-token",
    "chunk_size": 50,  # [max piwik payload size = 64k] / [max querystring size = 750]
}

STATS_PIWIK_EXPORT_ENABLED = False

STATS_SEARCH_HOST_CONNECTION_OPTIONS = {
    "timeout": 60,
}
