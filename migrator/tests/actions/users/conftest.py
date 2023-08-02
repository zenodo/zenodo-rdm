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
                "op": "u",
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
                "op": "u",
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
                "op": "u",
                "ts_ms": 1690906459854,
                "transaction": {
                    "id": "559140515:1444875976392",
                    "total_order": 2,
                    "data_collection_order": 2,
                },
            },
        ],
    }
