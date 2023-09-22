# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Transform actions module."""

from .communities import (
    CommunityCreateAction,
    CommunityDeleteAction,
    CommunityUpdateAction,
)
from .drafts import DraftCreateAction, DraftEditAction, DraftPublishAction
from .files import DraftFileUploadAction
from .github import (
    HookEventCreateAction,
    HookEventUpdateAction,
    HookRepoUpdateAction,
    ReleaseReceiveAction,
    ReleaseUpdateAction,
)
from .oauth import (
    OAuthApplicationCreateAction,
    OAuthApplicationDeleteAction,
    OAuthApplicationUpdateAction,
    OAuthGHDisconnectToken,
    OAuthLinkedAccountConnectAction,
    OAuthLinkedAccountDisconnectAction,
    OAuthServerTokenCreateAction,
    OAuthServerTokenDeleteAction,
    OAuthServerTokenUpdateAction,
)
from .users import USER_ACTIONS
from .ignored import IGNORED_ACTIONS

__all__ = (
    "CommunityCreateAction",
    "CommunityDeleteAction",
    "CommunityUpdateAction",
    "DraftCreateAction",
    "DraftEditAction",
    "DraftFileUploadAction",
    "DraftPublishAction",
    "HookEventCreateAction",
    "HookEventUpdateAction",
    "HookRepoUpdateAction",
    "OAuthApplicationCreateAction",
    "OAuthApplicationDeleteAction",
    "OAuthApplicationUpdateAction",
    "OAuthGHDisconnectToken",
    "OAuthLinkedAccountConnectAction",
    "OAuthLinkedAccountDisconnectAction",
    "OAuthServerTokenCreateAction",
    "OAuthServerTokenDeleteAction",
    "OAuthServerTokenUpdateAction",
    "ReleaseReceiveAction",
    "ReleaseUpdateAction",
    "IGNORED_ACTIONS",
    "USER_ACTIONS",
)
