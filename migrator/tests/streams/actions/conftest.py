# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

import pytest
from invenio_rdm_migrator.state import GLOBAL, State, StateEntity
from invenio_rdm_migrator.streams.records.state import ParentModelValidator


# FIXME: deduplicate code allowing invenio-rdm-migrator to define re-usable fixtures
@pytest.fixture(scope="function")
def state(tmp_dir):
    """Yields a state.

    Do not call `save` on this fixture. The in memory database will be reset on each
    function, therefore no information will be persisted from test to test.
    """
    state = State(db_dir=tmp_dir.name, validators={"parents": ParentModelValidator})

    return state


@pytest.fixture(scope="function")
def parents_state(state):
    """Records parent state.

    Keys are concept recids and values are dictionaries.
    """
    return StateEntity(state, "parents", "recid")


@pytest.fixture(scope="function")
def records_state(state):
    """Records state.

    Keys are recids and values are dictionaries.
    """
    return StateEntity(state, "records", "recid")


@pytest.fixture(scope="function")
def communities_state(state):
    """Communities state.

    Keys are community slugs and values are UUIDs.
    """
    return StateEntity(state, "communities", "slug")


@pytest.fixture(scope="function")
def pids_state(state):
    """Persistent identifiers state."""
    state = StateEntity(state, "pids", "pid_value")
    return state


@pytest.fixture(scope="function")
def global_state(state):
    """Records state.

    Keys are recids and values are dictionaries.
    """
    sq = StateEntity(state, "global", "key")
    GLOBAL.STATE = sq

    return sq
