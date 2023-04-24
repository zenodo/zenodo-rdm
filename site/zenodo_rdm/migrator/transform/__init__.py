# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator transformers."""


from .communities import ZenodoCommunityTransform
from .files import ZenodoFilesTransform
from .records import ZenodoRecordTransform
from .requests import ZenodoRequestTransform
from .users import ZenodoUserTransform

__all__ = (
    ZenodoCommunityTransform,
    ZenodoFilesTransform,
    ZenodoRecordTransform,
    ZenodoRequestTransform,
    ZenodoUserTransform,
)
