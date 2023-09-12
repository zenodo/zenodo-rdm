# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test OAuth action stream for RDM migration."""

import sqlalchemy as sa
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.models.oauth import ServerClient, ServerToken

from zenodo_rdm_migrator.transform.transactions import ZenodoTxTransform


def test_community_create_action_stream(
    database, session, pg_tx_load, test_extract_cls, tx_files
):
    stream = Stream(
        name="action",
        extract=test_extract_cls(tx_files["create"]),
        transform=ZenodoTxTransform(),
        load=pg_tx_load,
    )
    stream.run()

    assert session.scalars(sa.select(ServerClient)).one()
    assert session.scalars(sa.select(ServerToken)).one()
