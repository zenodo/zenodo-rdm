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
from invenio_rdm_migrator.streams.models.github import Release, Repository, WebhookEvent
from invenio_rdm_migrator.streams.models.oauth import ServerToken

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform

#
# Hooks
#


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


def test_github_hook_event_create(
    database, session, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["hook_enable_step2"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()
    assert session.scalars(sa.select(WebhookEvent)).one()


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


#
# Release
#


def test_receive_release(
    database, db_repository, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["release_receive"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    repo = db_repository.scalars(sa.select(Repository)).one()
    assert repo.updated.isoformat() == "2023-09-20T11:52:48.809652"
    assert db_repository.scalars(sa.select(Release)).one()


@pytest.fixture(scope="function")
def db_release(database, session):
    repo = Release(
        created="2022-01-01T00:00:00",
        updated="2022-01-01T00:00:00",
        id="c9fc85cd-e8ec-4ba0-9a13-75a590f3fd15",
        release_id=121854239,
        tag="v4",
        errors=None,
        repository_id="0d1b629d-7992-4650-b0b0-8908a0322bca",
        event_id="1e596bad-1bb3-4749-8a5e-dd9f1552ebc2",
        record_id=None,
        status="R",
    )

    session.add(repo)
    session.commit()

    return session


def test_update_release(database, db_release, pg_tx_load, test_extract_cls, tx_files):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["release_update"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    release = db_release.scalars(sa.select(Release)).one()
    assert release.status == "P"
