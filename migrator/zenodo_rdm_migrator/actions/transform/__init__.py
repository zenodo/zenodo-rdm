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
from .oauth import OAuthServerTokenCreateAction
from .users import UserDeactivationAction, UserEditAction, UserRegistrationAction

__all__ = (
    "CommunityCreateAction",
    "CommunityDeleteAction",
    "CommunityUpdateAction",
    "DraftCreateAction",
    "DraftEditAction",
    "DraftFileUploadAction",
    "DraftPublishAction",
    "UserDeactivationAction",
    "UserEditAction",
    "UserRegistrationAction",
)
