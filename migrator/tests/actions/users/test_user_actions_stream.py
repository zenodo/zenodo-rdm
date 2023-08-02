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
from invenio_rdm_migrator.streams.models.users import LoginInformation, User

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform

DB_URI = "postgresql+psycopg://invenio:invenio@localhost:5432/invenio"


@pytest.fixture(scope="function")
def db_engine():
    tables = [LoginInformation, User]
    eng = sa.create_engine(DB_URI)

    # create tables
    for model in tables:
        model.__table__.create(bind=eng, checkfirst=True)

    yield eng

    # remove tables
    for model in tables:
        model.__table__.drop(eng)


def test_user_register_action_stream(
    secret_keys_state, test_extract_cls, register_user_tx, db_engine
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
