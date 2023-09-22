# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test draft actions for RDM migration."""


from invenio_rdm_migrator.extract import Tx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from zenodo_rdm_migrator.actions.transform.files import DraftFileUploadAction


def test_matches_with_valid_data(file_upload_tx):
    assert (
        DraftFileUploadAction.matches_action(
            Tx(id=file_upload_tx["tx_id"], operations=file_upload_tx["operations"])
        )
        is True
    )


def test_matches_with_invalid_data(secret_keys_state):
    missing_buckets = [
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
    ]
    missing_one_bucket = [
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
    ]

    extra_bucket = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
    ]

    missing_ovs = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
    ]
    missing_one_ov = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
    ]

    extra_ov = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
    ]

    missing_fis = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
    ]
    missing_one_fi = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
    ]

    extra_fi = [
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_object"}, "op": OperationType.INSERT},
        {"source": {"table": "files_files"}, "op": OperationType.INSERT},
        {"source": {"table": "files_object"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_bucket"}, "op": OperationType.UPDATE},
        {"source": {"table": "files_files"}, "op": OperationType.UPDATE},
    ]

    for invalid_ops in [
        missing_buckets,
        missing_one_bucket,
        extra_bucket,
        missing_ovs,
        missing_one_ov,
        extra_ov,
        missing_fis,
        missing_one_fi,
        extra_fi,
    ]:
        assert (
            DraftFileUploadAction.matches_action(Tx(id=1, operations=invalid_ops))
            is False
        )


def test_transform_with_valid_data(file_upload_tx):
    action = DraftFileUploadAction(
        Tx(id=file_upload_tx["tx_id"], operations=file_upload_tx["operations"])
    )
    assert isinstance(action.transform(), load.DraftFileUploadAction)
