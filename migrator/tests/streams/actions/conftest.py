# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrator tests configuration."""

import pytest
from invenio_rdm_migrator.state import STATE, StateDB, StateEntity
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
    STATE.initialized_state(state_db)

    return STATE
