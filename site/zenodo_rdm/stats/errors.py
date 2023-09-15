# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Deposit errors."""

from __future__ import absolute_import, print_function


class PiwikExportRequestError(Exception):
    """Error for failed requests on Piwik export."""

    def __init__(self, *args, **kwargs):
        """Initialize the error with first and last events' timestamps."""
        super(PiwikExportRequestError, self).__init__(*args)
        self.extra = kwargs["export_info"]
