# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test GitHub action stream for RDM migration."""

import pytest
import sqlalchemy as sa
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.github import Repository, WebhookEvent
from invenio_rdm_migrator.streams.models.oauth import ServerToken

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


@pytest.fixture(scope="function")
def db_repository(database, session):
    repo = Repository(
        created="2022-01-01T00:00:00",
        updated="2022-01-01T00:00:00",
        id="0d1b629d-7992-4650-b0b0-8908a0322bca",
        github_id=427018972,
        name="ppanero/zenodo-release-test",
        # the following None means the hook was removed, but it does not affect the tests
        user_id=None,
        hook=None,
    )

    session.add(repo)
    session.commit()

    return session


def test_github_hook_repo_update(
    database, db_repository, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["hook_enable_step1"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    repo = db_repository.scalars(sa.select(Repository)).one()
    assert repo.hook == 434420608
    assert repo.user_id == 86490


@pytest.fixture(scope="function")
def db_token(database, session):
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

    session.add(token)
    session.commit()

    return session


def test_github_hook_event_create(
    database, db_token, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["hook_enable_step2"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    token = db_token.scalars(sa.select(ServerToken)).one()
    assert token.expires
    assert db_token.scalars(sa.select(WebhookEvent)).one()


def test_github_hook_disable(
    database, db_repository, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["hook_disable"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    repo = db_repository.scalars(sa.select(Repository)).one()
    assert not repo.hook


@pytest.fixture(scope="function")
def db_hook_event(database, session):
    token = WebhookEvent(
        created="2022-01-01T00:00:00",
        updated="2022-01-01T00:00:00",
        id="189d88dd-22d9-40d1-b3af-9da4b2bc4870",
        receiver_id="github",
        user_id=86490,
        payload='{"action": "published", "release": {"body": "Zenodo testing migration"}}',
        payload_headers=None,
        response='{"status": 202, "message": "Accepted."}',
        response_headers=None,
        response_code=202,
    )

    session.add(token)
    session.commit()

    return session


def test_github_hook_event_update(
    database, db_hook_event, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["hook_update"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    hook = db_hook_event.scalars(sa.select(WebhookEvent)).one()
    assert hook.response_code == 409
