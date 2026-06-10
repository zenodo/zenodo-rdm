# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom logging handler for ZenodoRDM."""

import logging
from datetime import datetime, timezone

from flask import current_app
from invenio_search.proxies import current_search_client


class OpenSearchHandler(logging.Handler):
    """Open search handler for logs."""

    def __init__(self):
        """Constructor."""
        logging.Handler.__init__(self)

    def _build_index_name(self):
        """Build index name."""
        return f"{current_app.config.get('SEARCH_INDEX_PREFIX')}-{current_app.config.get('CUSTOM_LOGGING_INDEX')}"

    def emit(self, record):
        """Emit, take log action."""
        if record.levelname == "CUSTOM":
            key = record.msg.pop("key")
            document = {
                "timestamp": datetime.fromtimestamp(
                    record.created, timezone.utc
                ).isoformat(),
                "key": key,
                "context": record.msg,
            }

            current_search_client.index(
                index=self._build_index_name(),
                body=document,
            )
