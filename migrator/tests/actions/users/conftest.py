# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator user actions tests configuration."""

import pytest
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType


@pytest.fixture()
def register_user_tx():
    """Transaction data to register a users.

    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724568,
        "operations": [
            {
                "after": {
                    "user_id": 123456,
                    "username": "migration_test_again",
                    "displayname": "migration_test_again",
                    "full_name": "",
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1690906446964,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1444875706232","1444875765576"]',
                    "schema": "public",
                    "table": "userprofiles_userprofile",
                    "txId": 559140492,
                    "lsn": 1444875765576,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
            },
            {
                "after": {
                    "id": 123456,
                    "email": "someaddr@domain.org",
                    "password": "zmkNzdnG1PXP5C3dmZqlJw==",
                    "active": True,
                    "confirmed_at": None,
                    "last_login_at": None,
                    "current_login_at": None,
                    "last_login_ip": None,
                    "current_login_ip": None,
                    "login_count": None,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1690906446964,
                    "snapshot": "False",
                    "db": "zenodo",
                    "sequence": '["1444875706232","1444875751384"]',
                    "schema": "public",
                    "table": "accounts_user",
                    "txId": 559140492,
                    "lsn": 1444875751384,
                    "xmin": None,
                },
                "op": OperationType.INSERT,
            },
        ],
    }


@pytest.fixture()
def login_user_tx():
    """Transaction data for user login.

    Can be treated as a user update.
    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724568,
        "operations": [
            {
                "after": {
                    "id": 123456,
                    "email": "someaddr@domain.org",
                    "password": "zmkNzdnG1PXP5C3dmZqlJw==",
                    "active": True,
                    "confirmed_at": None,
                    "last_login_at": 1690906447550349,
                    "current_login_at": 1690906447550349,
                    "last_login_ip": None,
                    "current_login_ip": "192.0.238.78",
                    "login_count": 1,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1690906447556,
                    "snapshot": False,
                    "db": "zenodo",
                    "sequence": '["1444875783960","1444875783960"]',
                    "schema": "public",
                    "table": "accounts_user",
                    "txId": 559140493,
                    "lsn": 1444875783960,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1690906447715,
                "transaction": {
                    "id": "559140493:1444875783960",
                    "total_order": 1,
                    "data_collection_order": 1,
                },
            }
        ],
    }


@pytest.fixture()
def confirm_user_tx():
    """Transaction data for user confirmation.

    Can be treated as a user update.
    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724568,
        "operations": [
            # contains one login + confirm
            {
                "after": {
                    "id": 123456,
                    "email": "someaddr@domain.org",
                    "password": "zmkNzdnG1PXP5C3dmZqlJw==",
                    "active": True,
                    "confirmed_at": None,
                    "last_login_at": 1690906447550349,
                    "current_login_at": 1690906459606401,
                    "last_login_ip": "192.0.238.78",
                    "current_login_ip": "192.0.238.78",
                    "login_count": 2,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1690906459615,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1444875944072","1444875976096"]',
                    "schema": "public",
                    "table": "accounts_user",
                    "txId": 559140515,
                    "lsn": 1444875976096,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1690906459854,
                "transaction": {
                    "id": "559140515:1444875976096",
                    "total_order": 1,
                    "data_collection_order": 1,
                },
            },
            {
                "after": {
                    "id": 123456,
                    "email": "someaddr@domain.org",
                    "password": "zmkNzdnG1PXP5C3dmZqlJw==",
                    "active": True,
                    "confirmed_at": 1690906459612306,
                    "last_login_at": 1690906447550349,
                    "current_login_at": 1690906459606401,
                    "last_login_ip": "192.0.238.78",
                    "current_login_ip": "192.0.238.78",
                    "login_count": 2,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1690906459615,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1444875944072","1444875976392"]',
                    "schema": "public",
                    "table": "accounts_user",
                    "txId": 559140515,
                    "lsn": 1444875976392,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1690906459854,
                "transaction": {
                    "id": "559140515:1444875976392",
                    "total_order": 2,
                    "data_collection_order": 2,
                },
            },
        ],
    }


@pytest.fixture()
def change_user_profile_tx():
    """Transaction data for user confirmation.

    Can be treated as a user update.
    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724568,
        "operations": [
            {
                "after": {
                    "user_id": 123456,
                    "username": "test_mig_ration",
                    "displayname": "test_mig_ration",
                    "full_name": "Some new full name",  # change full_name
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051405529,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447963025504","1447963025544"]',
                    "schema": "public",
                    "table": "userprofiles_userprofile",
                    "txId": 559790797,
                    "lsn": 1447963025544,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1691051405990,
                "transaction": {
                    "id": "559790797:1447963025544",
                    "total_order": 1,
                    "data_collection_order": 1,
                },
            },
            {
                "after": {
                    "user_id": 123456,
                    "username": "another_mig_username",  # change username
                    "displayname": "another_mig_username",
                    "full_name": "Some new full name",
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051420594,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447969038848","1447969038888"]',
                    "schema": "public",
                    "table": "userprofiles_userprofile",
                    "txId": 559791611,
                    "lsn": 1447969038888,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1691051420690,
                "transaction": {
                    "id": "559791611:1447969038888",
                    "total_order": 1,
                    "data_collection_order": 1,
                },
            },
        ],
    }


@pytest.fixture()
def change_user_email_tx():
    """Transaction data for user confirmation.

    Can be treated as a user update.
    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724568,
        "operations": [
            {
                "after": {
                    "id": 123456,
                    "email": "somenewaddr@domain.org",
                    "password": "zmkNzdnG1PXP5C3dmZqlJw==",
                    "active": True,
                    "confirmed_at": None,  # changing email un-confirms the user
                    "last_login_at": 1691051258769502,
                    "current_login_at": 1691051269040966,
                    "last_login_ip": "192.0.238.78",
                    "current_login_ip": "192.0.238.78",
                    "login_count": 2,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051428956,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447969535200","1447969540936"]',
                    "schema": "public",
                    "table": "accounts_user",
                    "txId": 559792087,
                    "lsn": 1447969540936,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1691051429304,
                "transaction": {
                    "id": "559792087:1447969540936",
                    "total_order": 1,
                    "data_collection_order": 1,
                },
            }
        ],
    }


@pytest.fixture()
def user_deactivation_tx():
    """Transaction data for user confirmation.

    Can be treated as a user update.
    As it would be after the extraction step.
    """
    return {
        "tx_id": 533724568,
        "operations": [
            {
                "after": {
                    "id": 123456,
                    "email": "ppanero27+testingmoremore@gmail.com",
                    "password": "zmkNzdnG1PXP5C3dmZqlJw==",
                    "active": False,
                    "confirmed_at": 1691051452717105,
                    "last_login_at": 1691051269040966,
                    "current_login_at": 1691051452710434,
                    "last_login_ip": "192.0.238.78",
                    "current_login_ip": "192.0.238.78",
                    "login_count": 3,
                },
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051494292,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447988344328","1447988266728"]',
                    "schema": "public",
                    "table": "accounts_user",
                    "txId": 559802332,
                    "lsn": 1447988266728,
                    "xmin": None,
                },
                "op": OperationType.UPDATE,
                "ts_ms": 1691051494531,
                "transaction": {
                    "id": "559802332:1447988266728",
                    "total_order": 1,
                    "data_collection_order": 1,
                },
            },
            {
                "before": {
                    "created": 0,
                    "updated": 0,
                    "sid_s": "bc51d8ea3ccc285c_64cb64fa",
                    "user_id": None,
                    "browser": None,
                    "browser_version": None,
                    "country": None,
                    "device": None,
                    "ip": None,
                    "os": None,
                },
                "after": None,
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051494292,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447988344328","1447988343624"]',
                    "schema": "public",
                    "table": "accounts_user_session_activity",
                    "txId": 559802332,
                    "lsn": 1447988343624,
                    "xmin": None,
                },
                "op": OperationType.DELETE,
                "ts_ms": 1691051494531,
                "transaction": {
                    "id": "559802332:1447988343624",
                    "total_order": 2,
                    "data_collection_order": 1,
                },
            },
            {
                "before": {
                    "created": 0,
                    "updated": 0,
                    "sid_s": "754493997337aa0a_64cb65bc",
                    "user_id": None,
                    "browser": None,
                    "browser_version": None,
                    "country": None,
                    "device": None,
                    "ip": None,
                    "os": None,
                },
                "after": None,
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051494292,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447988344328","1447988343816"]',
                    "schema": "public",
                    "table": "accounts_user_session_activity",
                    "txId": 559802332,
                    "lsn": 1447988343816,
                    "xmin": None,
                },
                "op": OperationType.DELETE,
                "ts_ms": 1691051494531,
                "transaction": {
                    "id": "559802332:1447988343816",
                    "total_order": 4,
                    "data_collection_order": 3,
                },
            },
            {
                "before": {
                    "created": 0,
                    "updated": 0,
                    "sid_s": "339a23457a4a7c59_64cb6505",
                    "user_id": None,
                    "browser": None,
                    "browser_version": None,
                    "country": None,
                    "device": None,
                    "ip": None,
                    "os": None,
                },
                "after": None,
                "source": {
                    "version": "2.3.0.Final",
                    "connector": "postgresql",
                    "name": "zenodo-migration",
                    "ts_ms": 1691051494292,
                    "snapshot": "false",
                    "db": "zenodo",
                    "sequence": '["1447988344328","1447988343720"]',
                    "schema": "public",
                    "table": "accounts_user_session_activity",
                    "txId": 559802332,
                    "lsn": 1447988343720,
                    "xmin": None,
                },
                "op": OperationType.DELETE,
                "ts_ms": 1691051494531,
                "transaction": {
                    "id": "559802332:1447988343720",
                    "total_order": 3,
                    "data_collection_order": 2,
                },
            },
        ],
    }
