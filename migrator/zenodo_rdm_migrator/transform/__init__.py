# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo migrator transformers."""


from .communities import ZenodoCommunityTransform
from .records import ZenodoDeletedRecordTransform, ZenodoRecordTransform
from .requests import ZenodoRequestTransform
from .users import ZenodoUserTransform

__all__ = (
    ZenodoCommunityTransform,
    ZenodoRecordTransform,
    ZenodoRequestTransform,
    ZenodoUserTransform,
    ZenodoDeletedRecordTransform,
)
