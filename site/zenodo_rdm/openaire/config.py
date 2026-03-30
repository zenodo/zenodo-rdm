# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenAire related configs."""

OPENAIRE_API_URL = "http://dev.openaire.research-infrastructures.eu/is/mvc/api"
"""OpenAIRE API endpoint."""

OPENAIRE_API_CREDENTIALS = {"username": "CHANGE_ME", "password": "CHANGE_ME"}
"""API credentials."""

# Beta configs
OPENAIRE_API_URL_BETA = None

# Other configs
OPENAIRE_PORTAL_URL = "https://explore.openaire.eu"
"""OpenAIRE portal url."""

OPENAIRE_DIRECT_INDEXING_ENABLED = False
"""Enable sending published records for direct indexing at OpenAIRE."""
