# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Base class for ML models."""


class MLModel:
    """Base class for ML models."""

    def __init__(self, version=None, **kwargs):
        """Constructor."""
        self.version = version

    def process(self, data, preprocess=None, postprocess=None, raise_exc=True):
        """Pipeline function to call pre/post process with predict."""
        try:
            preprocessor = preprocess or self.preprocess
            postprocessor = postprocess or self.postprocess

            preprocessed = preprocessor(data)
            prediction = self.predict(preprocessed)
            return postprocessor(prediction)
        except Exception as e:
            if raise_exc:
                raise e
            return None

    def predict(self, data):
        """Predict method to be implemented by subclass."""
        raise NotImplementedError()

    def preprocess(self, data):
        """Preprocess data."""
        return data

    def postprocess(self, data):
        """Postprocess data."""
        return data
