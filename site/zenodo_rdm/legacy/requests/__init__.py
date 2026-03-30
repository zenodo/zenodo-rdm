# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Request types for ZenodoRDM."""

from .community_manage_record import CommunityManageRecord
from .record_upgrade import LegacyRecordUpgrade

__all__ = ("LegacyRecordUpgrade", "CommunityManageRecord")
