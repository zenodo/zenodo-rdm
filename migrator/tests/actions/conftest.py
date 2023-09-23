# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

from pathlib import Path

import dictdiffer
import jsonlines
import pytest
from invenio_rdm_migrator.extract import Extract, Tx
from invenio_rdm_migrator.load.postgresql.transactions import PostgreSQLTx
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.state import STATE, StateDB
from invenio_rdm_migrator.streams.models.communities import (
    Community,
    CommunityFile,
    CommunityMember,
    FeaturedCommunity,
    RDMParentCommunityMetadata,
)
from invenio_rdm_migrator.streams.models.files import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)
from invenio_rdm_migrator.streams.models.github import Release, Repository, WebhookEvent
from invenio_rdm_migrator.streams.models.oai import OAISet
from invenio_rdm_migrator.streams.models.oauth import (
    RemoteAccount,
    RemoteToken,
    ServerClient,
    ServerToken,
)
from invenio_rdm_migrator.streams.models.pids import PersistentIdentifier
from invenio_rdm_migrator.streams.models.records import (
    RDMDraftFile,
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMVersionState,
)
from invenio_rdm_migrator.streams.models.users import (
    LoginInformation,
    SessionActivity,
    User,
    UserIdentity,
)
from invenio_rdm_migrator.streams.records.state import ParentModelValidator


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
    STATE.initialized_state(state_db, cache=False, search_cache=False)

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
def buckets_state(state):
    """Adds a bucket to draft map to the state."""
    state.BUCKETS.add(
        "0e12b4b6-9cc7-46df-9a04-c11c478de211",
        {"draft_id": "d94f793c-47d2-48e2-9867-ca597b4ebb41"},
    )
    return state


@pytest.fixture(scope="function")
def test_extract_cls():
    """Extract class with customizable tx."""

    class TestExtract(Extract):
        """Test extractor."""

        def __init__(self, txs, filter_unchanged=True):
            self.txs = txs if isinstance(txs, list) else [txs]
            self.filter_unchanged = filter_unchanged

        # NOTE: Copied from KafkaExtract
        def _filter_unchanged_values(self, op):
            before = op.get("before")
            if self.filter_unchanged and op["op"] == OperationType.UPDATE and before:
                after = op["after"]
                pk_keys = set(op["key"].keys())
                diff = dictdiffer.diff(before, after, ignore=pk_keys)
                changed_keys = {key for diff_op, key, _ in diff if diff_op == "change"}
                for key in (before.keys() | after.keys()) - (changed_keys | pk_keys):
                    before.pop(key)
                    after.pop(key)
            return op

        def run(self):
            """Yield one element at a time."""
            for tx in self.txs:
                if isinstance(tx, dict):
                    tx = tx
                if isinstance(tx, (str, Path)):
                    tx_path = Path(tx)
                    assert tx_path.exists()
                    with jsonlines.open(tx_path) as tx_ops:
                        tx = {
                            "operations": [
                                {"key": op["key"], **op["value"]} for op in tx_ops
                            ]
                        }
                        # convert "op" to OperationType enum
                        for op in tx["operations"]:
                            op["op"] = OperationType(op["op"].upper())
                        # extract the tx_id
                        tx["tx_id"] = tx["operations"][0]["source"]["txId"]
                yield Tx(
                    id=tx["tx_id"],
                    operations=list(
                        map(self._filter_unchanged_values, tx["operations"])
                    ),
                )

    return TestExtract


@pytest.fixture(scope="session")
def database(engine):
    """Setup database.

    Scope: module

    Normally, tests should use the function-scoped :py:data:`db` fixture
    instead. This fixture takes care of creating the database/tables and
    removing the tables once tests are done.
    """
    tables = [
        Community,
        CommunityFile,
        CommunityMember,
        FeaturedCommunity,
        FilesBucket,
        FilesInstance,
        FilesObjectVersion,
        LoginInformation,
        OAISet,
        PersistentIdentifier,
        RDMDraftMetadata,
        RDMDraftFile,
        RDMParentMetadata,
        RDMVersionState,
        RDMParentCommunityMetadata,
        RemoteAccount,
        RemoteToken,
        Release,
        Repository,
        ServerClient,
        ServerToken,
        SessionActivity,
        User,
        UserIdentity,
        WebhookEvent,
    ]

    # create tables
    for model in tables:
        model.__table__.create(bind=engine, checkfirst=True)

    yield

    # remove tables
    for model in tables:
        model.__table__.drop(engine)


@pytest.fixture(scope="function")
def pg_tx_load(db_uri, session):
    """Load instance configured with the DB session fixture."""
    return PostgreSQLTx(db_uri, _session=session, dry=False)
