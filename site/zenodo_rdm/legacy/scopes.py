# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OAuth2 legacy token scopes."""

from invenio_i18n import lazy_gettext as _
from invenio_oauth2server.models import Scope

deposit_write_scope = Scope(
    id_="deposit:write",
    group="deposit",
    help_text=_("Allow upload (but not publishing)."),
)
"""Allow upload (but not publishing)."""

deposit_actions_scope = Scope(
    id_="deposit:actions",
    group="deposit",
    help_text=_("Allow publishing of uploads."),
)
"""Allow publishing of uploads."""
