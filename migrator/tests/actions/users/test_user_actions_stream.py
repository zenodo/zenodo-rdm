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

DB_URI = "postgresql+psycopg://invenio:invenio@localhost:5432/invenio"


@pytest.fixture(scope="module")
def db_engine():
    tables = [LoginInformation, SessionActivity, User]
    eng = sa.create_engine(DB_URI)

    # create tables
    for model in tables:
        model.__table__.create(bind=eng, checkfirst=True)

    yield eng

    # remove tables
    for model in tables:
        model.__table__.drop(eng)


@pytest.fixture(scope="function")
def db_sessions(db_engine):
    sessions_data = [
        {
            "created": 1691051452717105,
            "updated": 1691051452717105,
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
            "created": 1691051452717105,
            "updated": 1691051452717105,
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
        "created": 1640995200000000,
        "updated": 1640995200000000,
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
    secret_keys_state, db_engine, test_extract_cls, register_user_tx
):
    test_extract_cls.tx = register_user_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(DB_URI),
    )
    stream.run()

    with db_engine.connect() as conn:
        # User
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        assert list(users)[0]._mapping["id"] == 123456

        # Login information
        loginfo = list(conn.execute(sa.select(LoginInformation)))
        assert len(loginfo) == 1
        assert list(loginfo)[0]._mapping["user_id"] == 123456

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
    secret_keys_state, db_user, test_extract_cls, login_user_tx, db_engine
):
    test_extract_cls.tx = login_user_tx

    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(DB_URI),
    )
    stream.run()

    with db_engine.connect() as conn:
        # Login information
        loginfo = list(conn.execute(sa.select(LoginInformation)))
        assert len(loginfo) == 1
        loginfo = list(loginfo)[0]._mapping
        assert loginfo["last_login_at"] == "1690906447550349"
        assert loginfo["current_login_at"] == "1690906447550349"
        assert loginfo["last_login_ip"] == None
        assert loginfo["current_login_ip"] == "192.0.238.78"
        assert loginfo["login_count"] == 1


def test_confirm_user_action_stream(
    secret_keys_state, db_user, test_extract_cls, confirm_user_tx, db_engine
):
    test_extract_cls.tx = confirm_user_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(DB_URI),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        assert list(users)[0]._mapping["confirmed_at"] == "1690906459612306"


@pytest.mark.skip("ZenodoUserProfileEditAction not implemented yet")
def test_change_user_profile_stream(
    db_user, test_extract_cls, change_user_profile_tx, db_engine
):
    test_extract_cls.tx = change_user_profile_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(DB_URI),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        user = list(users)[0]._mapping
        assert user["username"] == "another_mig_username"
        assert user["displayname"] == "another_mig_username"
        assert user["full_name"] == "Some new full name"


def test_confirm_user_action_stream(
    secret_keys_state, db_user, test_extract_cls, change_user_email_tx, db_engine
):
    test_extract_cls.tx = change_user_email_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(DB_URI),
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
    test_extract_cls,
    user_deactivation_tx,
    db_engine,
):
    test_extract_cls.tx = user_deactivation_tx
    stream = Stream(
        name="action",
        extract=test_extract_cls(),
        transform=ZenodoTxTransform(),
        load=PostgreSQLTx(DB_URI),
    )
    stream.run()

    with db_engine.connect() as conn:
        users = list(conn.execute(sa.select(User)))
        assert len(users) == 1
        assert list(users)[0]._mapping["active"] == False

        sessions = list(conn.execute(sa.select(SessionActivity)))
        assert len(sessions) == 0
