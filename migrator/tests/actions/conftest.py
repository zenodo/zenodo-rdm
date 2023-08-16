# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

import pytest
from invenio_rdm_migrator.extract import Extract, Tx
from invenio_rdm_migrator.state import STATE, StateDB
from invenio_rdm_migrator.streams.models.files import FilesBucket
from invenio_rdm_migrator.streams.models.pids import PersistentIdentifier
from invenio_rdm_migrator.streams.models.records import (
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMVersionState,
)
from invenio_rdm_migrator.streams.models.users import (
    LoginInformation,
    SessionActivity,
    User,
)
from invenio_rdm_migrator.streams.records.state import ParentModelValidator
from sqlalchemy import create_engine


# FIXME: deduplicate code allowing invenio-rdm-migrator to define re-usable fixtures
@pytest.fixture(scope="function")
def state(tmp_dir):
    """Yields a state.

    Do not call `save` on this fixture. The in memory database will be reset on each
    function, therefore no information will be persisted from test to test.
    """
    state_db = StateDB(
        db_dir=tmp_dir.name, validators={"parents": ParentModelValidator}
    )
    STATE.initialized_state(state_db)

    return STATE


@pytest.fixture(scope="function")
def secret_keys_state(state):
    """Adds secret keys to global state."""
    state.VALUES.add(
        "old_secret_key",
        {"value": bytes("OLDKEY", "utf-8")},
    )
    state.VALUES.add(
        "new_secret_key",
        {"value": bytes("NEWKEY", "utf-8")},
    )
    return


@pytest.fixture(scope="function")
def test_extract_cls():
    """Extract class with customizable tx."""

    class TestExtractor(Extract):
        """Test extractor."""

        tx = None
        """Must be set before usage.qwa"""

        def run(self):
            """Yield one element at a time."""
            yield Tx(id=self.tx["tx_id"], operations=self.tx["operations"])

    return TestExtractor


@pytest.fixture(scope="session")
def db_uri():
    """Database connection string."""
    return "postgresql+psycopg://invenio:invenio@localhost:5432/invenio"


@pytest.fixture(scope="function")
def db_engine(db_uri):
    """Setup database.

    Scope: module

    Normally, tests should use the function-scoped :py:data:`db` fixture
    instead. This fixture takes care of creating the database/tables and
    removing the tables once tests are done.
    """
    tables = [
        FilesBucket,
        LoginInformation,
        PersistentIdentifier,
        RDMDraftMetadata,
        RDMParentMetadata,
        RDMVersionState,
        SessionActivity,
        User,
    ]
    eng = create_engine(db_uri)

    # create tables
    for model in tables:
        model.__table__.create(bind=eng, checkfirst=True)

    yield eng

    # remove tables
    for model in tables:
        model.__table__.drop(eng)
