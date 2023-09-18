# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zendo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAire related configs."""

# OpenAIRE API configs
OPENAIRE_API_USERNAME = ""
"""OpenAIRE API authentication - username."""

OPENAIRE_API_PASSWORD = ""
"""OpenAIRE API authentication - password."""

OPENAIRE_API_URL = "http://dev.openaire.research-infrastructures.eu/is/mvc/api/results"
"""OpenAIRE API endpoint."""

# Beta configs
OPENAIRE_API_URL_BETA = None

# Other configs
OPENAIRE_COMMUNITIES = {}
"""OpenAIRE communities resource subtypes configuration."""

OPENAIRE_PORTAL_URL = "https://explore.openaire.eu"
"""OpenAIRE portal url."""

OPENAIRE_DIRECT_INDEXING_ENABLED = False
"""Enable sending published records for direct indexing at OpenAIRE."""
