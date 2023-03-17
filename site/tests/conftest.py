# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures."""

from collections import namedtuple

import pytest
from flask_security import login_user
from flask_security.utils import hash_password
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api as _create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


RunningApp = namedtuple(
    "RunningApp",
    [
        "app",
        "location",
        "cache",
    ],
)


@pytest.fixture
def running_app(
    app,
    location,
    cache,
):
    """Fixture provides an app with the typically needed db data loaded.

    All of these fixtures are often needed together, so collecting them
    under a semantic umbrella makes sense.
    """
    return RunningApp(
        app,
        location,
        cache,
    )


@pytest.fixture
def test_app(running_app):
    """Get current app."""
    return running_app.app


@pytest.fixture()
def users(app, db):
    """Create example users."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        user1 = datastore.create_user(
            email="info@zenodo.org",
            password=hash_password("password"),
            active=True,
        )

    db.session.commit()
    return [user1]


@pytest.fixture()
def client_with_login(client, users):
    """Log in a user to the client."""
    user = users[0]
    login_user(user)
    login_user_via_session(client, email=user.email)
    return client
