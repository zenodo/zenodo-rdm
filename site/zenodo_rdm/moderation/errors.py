# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Errors for moderation."""


class ModerationException(Exception):
    """Base exception for moderation errors."""


class UserBlockedException(ModerationException):
    """User is blocked."""
