# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Model definitions."""


import json
import string

import requests
from bs4 import BeautifulSoup
from flask import current_app

from .base import MLModel


class SpamDetectorScikit(MLModel):
    """Spam detection model based on Sklearn."""

    MODEL_NAME = "sklearn-spam"
    MAX_WORDS = 4000

    def __init__(self, version, **kwargs):
        """Constructor. Makes version required."""
        super().__init__(version, **kwargs)

    def preprocess(self, data):
        """Preprocess data.

        Parse HTML, remove punctuation and truncate to max chars.
        """
        text = BeautifulSoup(data, "html.parser").get_text()
        trans_table = str.maketrans(string.punctuation, " " * len(string.punctuation))
        parts = text.translate(trans_table).lower().strip().split(" ")
        if len(parts) >= self.MAX_WORDS:
            parts = parts[: self.MAX_WORDS]
        return " ".join(parts)

    def postprocess(self, data):
        """Postprocess data.

        Gives spam and ham probability.
        """
        result = {
            "spam": data["outputs"][0]["data"][0],
            "ham": data["outputs"][0]["data"][1],
        }
        return result

    def _send_request_kubeflow(self, data):
        """Send predict request to Kubeflow."""
        payload = {
            "inputs": [
                {
                    "name": "input-0",
                    "shape": [1],
                    "datatype": "BYTES",
                    "data": [f"{data}"],
                }
            ]
        }
        model_ref = self.MODEL_NAME + "-" + self.version
        url = current_app.config.get("ML_KUBEFLOW_MODEL_URL").format(model_ref)
        host = current_app.config.get("ML_KUBEFLOW_MODEL_HOST").format(model_ref)
        access_token = current_app.config.get("ML_KUBEFLOW_TOKEN")
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Host": host,
            },
            json=payload,
        )
        if r.status_code != 200:
            raise requests.RequestException("Prediction was not successful.", request=r)
        return json.loads(r.text)

    def predict(self, data):
        """Get prediction from model."""
        prediction = self._send_request_kubeflow(data)
        return prediction
