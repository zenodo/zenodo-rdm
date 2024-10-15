#
# Copyright (C) 2023 CERN.
#
# Zendo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
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
