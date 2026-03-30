# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Deposit errors."""


class PiwikExportRequestError(Exception):
    """Error for failed requests on Piwik export."""

    def __init__(self, *args, **kwargs):
        """Initialize the error with first and last events' timestamps."""
        super(PiwikExportRequestError, self).__init__(*args)
        self.extra = kwargs["export_info"]
