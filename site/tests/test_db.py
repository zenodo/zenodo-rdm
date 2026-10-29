# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-replica session routing tests."""

import os
import runpy
from pathlib import Path

import pytest
from flask_login import login_user
from invenio_db.shared import db as shared_db

from zenodo_rdm.db import routed_bind


@pytest.fixture(scope="module")
def app_config(app_config):
    """Configure a read replica bind pointing at the test database."""
    app_config["SQLALCHEMY_BINDS"] = {
        "read_replica": os.environ["INVENIO_SQLALCHEMY_DATABASE_URI"]
    }
    app_config["DB_SESSION_BIND_FUNC"] = routed_bind
    app_config["ZENODO_READ_REPLICA_ENDPOINTS"] = frozenset(
        ["invenio_app_rdm_records.record_detail"]
    )
    yield app_config
    # init_app registers the bind's metadata on the global ``db``; later modules'
    # apps lack the bind, so their create_all() would fail on it
    shared_db.metadatas.pop("read_replica")


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_anonymous_read_goes_to_replica(app, database, method):
    """Anonymous reads of allowlisted endpoints hit the replica via the session."""
    # ``database`` keeps invenio-db's session; the ``db`` fixture replaces get_bind
    with app.test_request_context("/records/12345", method=method):
        assert database.session.get_bind() is database.engines["read_replica"]


@pytest.mark.parametrize(
    "method,path",
    [
        # Writes must reach the primary
        ("POST", "/records/12345"),
        # Endpoint not in the allowlist
        ("GET", "/communities/test/members"),
    ],
)
def test_request_stays_on_primary(app, database, method, path):
    """Writes and non-allowlisted endpoints stay on the primary."""
    with app.test_request_context(path, method=method):
        assert database.session.get_bind() is database.engine


def test_authenticated_user_stays_on_primary(app, db, users):
    """Logged-in users read their own writes, so they stay on the primary."""
    with app.test_request_context("/records/12345"):
        login_user(users[0])
        assert routed_bind(db.session) is None


def test_outside_request_stays_on_primary(app, database):
    """CLI and Celery tasks (no request context) stay on the primary."""
    with app.app_context():
        assert database.session.get_bind() is database.engine


def test_members_endpoint_not_routed():
    """Community members endpoint stays off the replica allowlist."""
    cfg = runpy.run_path(str(Path(__file__).parents[2] / "invenio.cfg"))
    assert "invenio_communities.members" not in cfg["ZENODO_READ_REPLICA_ENDPOINTS"]
