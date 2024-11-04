# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Errors for moderation."""


class ModerationException(Exception):
    """Base exception for moderation errors."""


class UserBlockedException(ModerationException):
    """User is blocked."""
