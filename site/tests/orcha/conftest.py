# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Waitlist fixtures."""

from datetime import datetime

import pytest
from invenio_accounts.models import Role
from invenio_app import factory as app_factory


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return app_factory.create_app


@pytest.fixture()
def verified_user(UserFixture, app, db):
    """Verified user for waitlist test."""
    u = UserFixture(
        email="verified@inveniosoftware.org",
        password="verified",
        base_url="https://127.0.0.1:5000",
    )
    u.create(app, db)
    u.user.verified_at = datetime.utcnow()
    db.session.commit()
    return u

@pytest.fixture()
def orcha_waitlist_role(db):
    """Store 'orcha-waitlist' role.
    
    NOTE: In prod this role is created manually via existing CLI command.
    """
    role = Role(name="orcha-waitlist")
    db.session.add(role)
    db.session.commit()
    return role


@pytest.fixture()
def orcha_waitlisted_user(UserFixture, app, db, orcha_waitlist_role):
    """Verified user who has the orcha-waitlist role."""
    u = UserFixture(
        email="waitlisted@inveniosoftware.org",
        password="waitlisted",
        base_url="https://127.0.0.1:5000",
    )
    u.create(app, db)
    u.user.verified_at = datetime.utcnow()
    datastore = app.extensions["security"].datastore
    datastore.add_role_to_user(u.user, orcha_waitlist_role)
    db.session.commit()
    return u
