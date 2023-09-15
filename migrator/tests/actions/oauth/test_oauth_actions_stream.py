# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test OAuth action stream for RDM migration."""

import pytest
import sqlalchemy as sa
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.oauth import ServerClient, ServerToken

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform

##
# TOKENS
##


def test_oauth_server_token_create_action_stream(
    database, session, pg_tx_load, test_extract_cls, tx_files_tokens
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_tokens["create"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert session.scalars(sa.select(ServerClient)).one()
    assert session.scalars(sa.select(ServerToken)).one()


@pytest.fixture(scope="function")
def db_client_server(database, session):
    client = ServerClient(
        name="test-incremental-token",
        description="",
        website="",
        user_id=123456,
        client_id="SZLrR8ApZPeBjqj7uMB1JWXavhxebu6V0mwMtvMr",
        client_secret="cH4ng3D143BM6gKc29VN0rWZPI4wi0gHBcJQYdVNLtibTK0AR1ZWbWT5oYeQ",
        is_confidential=False,
        is_internal=True,
        _redirect_uris=None,
        _default_scopes="tokens:generate user:email",
    )

    token = ServerToken(
        id=156666,
        client_id="SZLrR8ApZPeBjqj7uMB1JWXavhxebu6V0mwMtvMr",
        user_id=123456,
        token_type="bearer",
        access_token="cH4ng3DzbXd4QTcrRjFMcTVMRHl3QlY2Rkdib0VwREY4aDhPcHo2dUt2ZnZ3OVVPa1BvRDl0L1NRZmFrdXNIU2hJR2JWc0NHZDZSVEhVT2JQcmdjS1E9PQ==",
        refresh_token=None,
        expires=None,
        _scopes="tokens:generate user:email",
        is_personal=True,
        is_internal=False,
    )

    session.add(client)
    session.add(token)
    session.commit()

    return session


def test_oauth_server_token_update_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_tokens
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_tokens["update"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    client = db_client_server.scalars(sa.select(ServerClient)).one()
    assert client.name == "test-incremental-token-too"

    token = db_client_server.scalars(sa.select(ServerToken)).one()
    assert token._scopes == ""


def test_oauth_server_token_delete_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_tokens
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_tokens["delete"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert not db_client_server.scalars(sa.select(ServerToken)).one_or_none()


##
# APPLICATIONS
##


def test_oauth_application_create_action_stream(
    database, session, pg_tx_load, test_extract_cls, tx_files_applications
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_applications["create"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    client = session.scalars(sa.select(ServerClient)).one()
    assert client.name == "test-application-migration"
    assert client._redirect_uris == "https://somewhere.com/authorize/"


def test_oauth_application_update_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_applications
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_applications["update"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    client = db_client_server.scalars(sa.select(ServerClient)).one()
    assert client.name == "test-application-migration-too"


def test_oauth_application_reset_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_applications
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_applications["reset"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    client = db_client_server.scalars(sa.select(ServerClient)).one()
    client.client_secret == "A5Vrx17x0k2IZDkcGu0UmeDk90Wesp22GM9c2WZBgynRPZY6UHTRL1ifZzU6"


def test_oauth_application_delete_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_applications
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_applications["delete"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert not db_client_server.scalars(sa.select(ServerClient)).one_or_none()
