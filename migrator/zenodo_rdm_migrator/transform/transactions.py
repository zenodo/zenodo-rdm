# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
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
