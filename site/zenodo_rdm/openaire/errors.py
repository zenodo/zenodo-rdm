# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""OpenAIRE errors."""


class OpenAIRERequestError(Exception):
    """Error for failed requests on the OpenAIRE API."""
