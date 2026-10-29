# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-replica routing without a configured replica bind."""

import pytest

from zenodo_rdm.db import routed_bind


@pytest.fixture(scope="module")
def app_config(app_config):
    """Install the routing hook without setting ``SQLALCHEMY_BINDS``."""
    app_config["DB_SESSION_BIND_FUNC"] = routed_bind
    app_config["ZENODO_READ_REPLICA_ENDPOINTS"] = frozenset(
        ["invenio_app_rdm_records.record_detail"]
    )
    return app_config


def test_unset_bind_reads_from_primary(app, database):
    """Without INVENIO_SQLALCHEMY_READ_REPLICA_URI, reads stay on the primary."""
    with app.test_request_context("/records/12345"):
        assert database.session.get_bind() is database.engine
