# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator loader."""

# FIXME: awards and funders should be moved to invenio-rdm-migrator
from .awards import ZenodoAwardsLoad
from .files import ZenodoFilesLoad
from .funders import ZenodoFundersLoad
from .transactions import ZenodoTransactionLoad

__all__ = (
    "ZenodoAwardsLoad",
    "ZenodoFilesLoad",
    "ZenodoFundersLoad",
    "ZenodoTransactionLoad",
)
