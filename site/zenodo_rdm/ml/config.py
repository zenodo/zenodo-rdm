# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Machine learning config."""

from .models import SpamDetectorScikit

ML_MODELS = {
    "spam_scikit": SpamDetectorScikit,
}
"""Machine learning models."""

# NOTE Model URL and model host need to be formattable strings for the model name.
ML_KUBEFLOW_MODEL_URL = "CHANGE-{0}-ME"
ML_KUBEFLOW_MODEL_HOST = "{0}-CHANGE"
ML_KUBEFLOW_TOKEN = "CHANGE SECRET"
"""Kubeflow connection config."""
