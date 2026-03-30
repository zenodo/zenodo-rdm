# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Transform actions module."""

from .communities import COMMUNITY_ACTIONS
from .drafts import DRAFT_ACTIONS
from .files import FILES_ACTIONS
from .github import GITHUB_ACTIONS
from .ignored import IGNORED_ACTIONS
from .oauth import OAUTH_ACTIONS
from .users import USER_ACTIONS

__all__ = (
    "DRAFT_ACTIONS",
    "FILES_ACTIONS",
    "GITHUB_ACTIONS",
    "OAUTH_ACTIONS",
    "COMMUNITY_ACTIONS",
    "IGNORED_ACTIONS",
    "USER_ACTIONS",
)
