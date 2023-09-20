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
from invenio_rdm_migrator.streams.models.oauth import (
    RemoteAccount,
    RemoteToken,
    ServerClient,
    ServerToken,
)
from invenio_rdm_migrator.streams.models.users import UserIdentity

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


#
# ORCID
#


def test_oauth_linked_app_connect_orcid_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_linked_accounts
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_linked_accounts["connect_orcid"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert db_client_server.scalars(sa.select(RemoteAccount)).one()
    assert db_client_server.scalars(sa.select(RemoteToken)).one()
    assert db_client_server.scalars(sa.select(UserIdentity)).one()


@pytest.fixture(scope="function")
def db_linked_orcid_account(database, session):
    remote_account = RemoteAccount(
        id=8546,
        user_id=22858,
        client_id="APP-MAX7XCD8Q98X4VT6",
        extra_data='{"orcid": "0000-0002-5676-5956", "full_name": "Alex Ioannidis"}',
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
    )

    remote_token = RemoteToken(
        id_remote_account=8546,
        token_type="",
        access_token="R3RVeGc3K0RrM25rbXc4ZWxGM3oxYVA4LzcwVWpCNkM4aG8vRy9CNWxkZFFCMk9OR1d2d29lN3dKdWk2eEVTQQ==",
        secret="",
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
    )

    user_identity = UserIdentity(
        id="0000-0002-5676-5956",
        method="orcid",
        id_user=22858,
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
    )

    session.add(remote_account)
    session.add(remote_token)
    session.add(user_identity)
    session.commit()

    return session


def test_oauth_linked_app_disconnect_orcid_action_stream(
    db_linked_orcid_account, pg_tx_load, test_extract_cls, tx_files_linked_accounts
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_linked_accounts["disconnect_orcid"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert not db_linked_orcid_account.scalars(sa.select(RemoteAccount)).one_or_none()
    assert not db_linked_orcid_account.scalars(sa.select(RemoteToken)).one_or_none()
    assert not db_linked_orcid_account.scalars(sa.select(UserIdentity)).one_or_none()


#
# GH
#


def test_oauth_linked_app_connect_gh_action_stream(
    db_client_server, pg_tx_load, test_extract_cls, tx_files_linked_accounts
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files_linked_accounts["connect_gh"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert db_client_server.scalars(sa.select(RemoteAccount)).one()
    assert db_client_server.scalars(sa.select(RemoteToken)).one()
    assert db_client_server.scalars(sa.select(UserIdentity)).one()
    assert db_client_server.scalars(sa.select(ServerClient)).one()
    assert db_client_server.scalars(sa.select(ServerToken)).one()


@pytest.fixture(scope="function")
def db_linked_gh_account(database, session):
    remote_account = RemoteAccount(
        id=8546,
        user_id=86490,
        client_id="APP-MAX7XCD8Q98X4VT6",
        extra_data='{"orcid": "0000-0002-5676-5956", "full_name": "Alex Ioannidis"}',
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
    )

    remote_token = RemoteToken(
        id_remote_account=8546,
        token_type="",
        access_token="R3RVeGc3K0RrM25rbXc4ZWxGM3oxYVA4LzcwVWpCNkM4aG8vRy9CNWxkZFFCMk9OR1d2d29lN3dKdWk2eEVTQQ==",
        secret="",
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
    )

    user_identity = UserIdentity(
        id="6756943",
        method="github",
        id_user=86490,
        created="2023-06-29T13:00:00",
        updated="2023-06-29T14:00:00",
    )

    server_token = ServerToken(
        id=157734,
        client_id="rKmVKlRxnQJfyizWeVKRO26cZjLqd2yWhsBFkjv0",
        user_id=86490,
        token_type="bearer",
        access_token="cH4ng3DzbXd4QTcrRjFMcTVMRHl3QlY2Rkdib0VwREY4aDhPcHo2dUt2ZnZ3OVVPa1BvRDl0L1NRZmFrdXNIU2hJR2JWc0NHZDZSVEhVT2JQcmdjS1E9PQ==",
        refresh_token=None,
        expires=None,
        _scopes="webhooks:event",
        is_personal=True,
        is_internal=False,
    )

    session.add(remote_account)
    session.add(remote_token)
    session.add(user_identity)
    session.add(server_token)
    session.commit()

    return session


def test_oauth_linked_app_disconnect_gh_action_stream(
    db_linked_gh_account, pg_tx_load, test_extract_cls, tx_files_linked_accounts
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(
            [
                tx_files_linked_accounts["disconnect_gh_client"],
                tx_files_linked_accounts["disconnect_gh_token"],
            ]
        ),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert not db_linked_gh_account.scalars(sa.select(RemoteAccount)).one_or_none()
    assert not db_linked_gh_account.scalars(sa.select(RemoteToken)).one_or_none()
    assert not db_linked_gh_account.scalars(sa.select(ServerToken)).one_or_none()
    assert not db_linked_gh_account.scalars(sa.select(UserIdentity)).one_or_none()
