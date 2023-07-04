# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator requests transformers."""

from functools import partial

from invenio_rdm_migrator.transform import IdentityTransform, TransactionGroup
from .records import ZenodoActionRecordTransform


table_transform_map = {
    "pidstore_pid": IdentityTransform(),
    "files_bucket": IdentityTransform(),
    "records_metadata": ZenodoActionRecordTransform(),
}

ZenodoTransactionGroupTransform = partial(TransactionGroup, table_transform_map)
