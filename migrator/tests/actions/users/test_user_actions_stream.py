# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test user actions stream."""

import pytest
import sqlalchemy as sa
from invenio_rdm_migrator.load.postgresql.transactions import PostgreSQLTx
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.users import (
    LoginInformation,
    SessionActivity,
    User,
)
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture(scope="function")
def db_sessions(db_engine):
    sessions_data = [
        {
            "created": "2023-08-03T08:30:52.717105",
            "updated": "2023-08-03T08:30:52.717105",
            "sid_s": "754493997337aa0a_64cb65bc",
            "user_id": 123456,
            "browser": None,
            "browser_version": None,
            "country": None,
            "device": None,
            "ip": None,
            "os": None,
        },
        {
            "created": "2023-08-03T08:30:52.717105",
            "updated": "2023-08-03T08:30:52.717105",
            "sid_s": "bc51d8ea3ccc285c_64cb64fa",
            "user_id": 123456,
            "browser": None,
            "browser_version": None,
            "country": None,
            "device": None,
            "ip": None,
            "os": None,
        },
    ]

    history = []
    with Session(db_engine) as session:
        for session_data in sessions_data:
            obj = SessionActivity(**session_data)
            history.append(obj)
            session.add(obj)
        session.commit()

    yield

    # cleanup
    with Session(db_engine) as session:
        for obj in history:
            session.delete(obj)

        try:
            session.commit()
        except ObjectDeletedError:  # might be deleted on user inactivation
            pass


@pytest.fixture(scope="function")
def db_user(db_engine):
    user_data = {
        "id": 123456,
        "created": "2023-08-01T16:14:06.964000",
        "updated": "2023-08-01T16:14:06.964000",
        "username": "test_user",
        "displayname": "test_user",
        "email": "someaddr@domain.org",
        "password": "zmkNzdnG1PXP5C3dmZqlJw==",
        "active": True,
        "confirmed_at": None,
        "version_id": 1,
        "profile": {"full_name": "User test"},
        "preferences": {
            "visibility": "restricted",
            "email_visibility": "restricted",
        },
    }

    log_info_data = {
        "user_id": 123456,
        "last_login_at": None,
        "current_login_at": None,
        "last_login_ip": None,
        "current_login_ip": None,
        "login_count": 0,
    }

    history = []
    with Session(db_engine) as session:
        user_obj = User(**user_data)
        history.append(user_obj)
        session.add(user_obj)
        log_info_obj = LoginInformation(**log_info_data)
        history.append(log_info_obj)
        session.add(log_info_obj)
        session.commit()

    yield

    # cleanup
    with Session(db_engine) as session:
        for obj in history:
            session.delete(obj)
        session.commit()


def test_user_register_action_stream(
    secret_keys_state, db_uri, db_engine, test_extract_cls, register_user_tx
):
    test_extract_cls.tx = register_user_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        # User
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        user = users[0]._mapping
        assert user["id"] == 123456
        assert user["created"] == "2023-08-01T16:14:06.964000"
        assert user["updated"] == "2023-08-01T16:14:06.964000"

        # Login information
        loginfo = list(conn.execute(sa.select(LoginInformation)))
        assert len(loginfo) == 1
        loginfo = loginfo[0]._mapping
        assert loginfo["user_id"] == 123456
        assert loginfo["last_login_at"] == None
        assert loginfo["current_login_at"] == None

        # cleanup
        # not ideal should be done more generically with a fixture
        conn.execute(sa.delete(User).where(User.__table__.columns.id == 123456))
        conn.execute(
            sa.delete(LoginInformation).where(
                LoginInformation.__table__.columns.user_id == 123456
            )
        )
        conn.commit()


def test_user_login_action_stream(
    secret_keys_state, db_user, db_uri, db_engine, test_extract_cls, login_user_tx
):
    test_extract_cls.tx = login_user_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        # Login information
        loginfo = list(conn.execute(sa.select(LoginInformation)))
        assert len(loginfo) == 1
        loginfo = list(loginfo)[0]._mapping
        assert loginfo["last_login_at"] == "2023-08-01T16:14:07.550349"
        assert loginfo["current_login_at"] == "2023-08-01T16:14:07.550349"
        assert loginfo["last_login_ip"] == None
        assert loginfo["current_login_ip"] == "192.0.238.78"
        assert loginfo["login_count"] == 1


def test_confirm_user_action_stream(
    secret_keys_state, db_user, db_uri, db_engine, test_extract_cls, confirm_user_tx
):
    test_extract_cls.tx = confirm_user_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        assert list(users)[0]._mapping["confirmed_at"] == "2023-08-01T16:14:19.612306"


@pytest.mark.skip("UserProfileEditAction not implemented yet")
def test_change_user_profile_stream(
    db_user, db_uri, db_engine, test_extract_cls, change_user_profile_tx
):
    test_extract_cls.tx = change_user_profile_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        user = list(users)[0]._mapping
        assert user["username"] == "another_mig_username"
        assert user["displayname"] == "another_mig_username"
        assert user["full_name"] == "Some new full name"


def test_edit_user_action_stream(
    secret_keys_state,
    db_user,
    db_uri,
    db_engine,
    test_extract_cls,
    change_user_email_tx,
):
    test_extract_cls.tx = change_user_email_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        assert list(users)[0]._mapping["email"] == "somenewaddr@domain.org"


def test_deactivate_user_action_stream(
    secret_keys_state,
    db_user,
    db_sessions,
    db_uri,
    db_engine,
    test_extract_cls,
    user_deactivation_tx,
):
    test_extract_cls.tx = user_deactivation_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(db_uri),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        assert list(users)[0]._mapping["active"] == False

        sessions = list(conn.execute(sa.select(SessionActivity)))
        assert len(sessions) == 0
