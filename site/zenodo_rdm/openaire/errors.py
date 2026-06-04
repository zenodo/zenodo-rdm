# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""OpenAIRE errors."""


class OpenAIRERequestError(Exception):
    """Error for failed requests on the OpenAIRE API."""


class OpenAIREInvalidRecordError(OpenAIRERequestError):
    """Record deterministically rejected by the OpenAIRE Direct Indexing API.

    OpenAIRE validates submitted records and rejects invalid ones with HTTP 400
    (missing mandatory fields) or 413 (overall body or per-field size limits).
    These rejections are deterministic, so retrying the same record never
    succeeds. The response body names the offending field and the limit.
    """

    def __init__(self, status_code, message):
        """Keep the status code so callers can tell 400 from 413."""
        self.status_code = status_code
        super().__init__(message)
