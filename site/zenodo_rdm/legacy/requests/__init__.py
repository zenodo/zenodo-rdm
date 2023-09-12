# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Request types for ZenodoRDM."""


from .community_manage_record import CommunityManageRecord
from .record_upgrade import LegacyRecordUpgrade

__all__ = ("LegacyRecordUpgrade", "CommunityManageRecord")
