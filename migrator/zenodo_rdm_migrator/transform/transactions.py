# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator actions transform."""


from invenio_rdm_migrator.transform import BaseTxTransform

from ..actions.transform import (
    COMMUNITY_ACTIONS,
    DRAFT_ACTIONS,
    FILES_ACTIONS,
    GITHUB_ACTIONS,
    IGNORED_ACTIONS,
    OAUTH_ACTIONS,
    USER_ACTIONS,
)


class ZenodoTxTransform(BaseTxTransform):
    """Zenodo transaction transform."""

    actions = [
        *GITHUB_ACTIONS,
        *FILES_ACTIONS,
        *DRAFT_ACTIONS,
        *COMMUNITY_ACTIONS,
        *OAUTH_ACTIONS,
        *USER_ACTIONS,
        *IGNORED_ACTIONS,
    ]
