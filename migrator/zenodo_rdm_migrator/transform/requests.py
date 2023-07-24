# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator requests transformers."""

from invenio_rdm_migrator.streams.requests import RequestTransform

from .entries.requests import ZenodoRequestEntry


class ZenodoRequestTransform(RequestTransform):
    """Transform a Zenodo request into RDM."""

    def _request(self, entry):
        """Transform the request."""
        return ZenodoRequestEntry().transform(entry)
