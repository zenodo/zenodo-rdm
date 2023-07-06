# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator transactions loader."""


from invenio_rdm_migrator.load.postgresql.transactions import PostgreSQLExecute
from invenio_rdm_migrator.load.postgresql.transactions.generators import (
    TransactionGroupGenerator,
)
from invenio_rdm_migrator.streams.transactions import FilesBucketRowGenerator
from invenio_rdm_migrator.streams.transactions.pids import PIDRowGenerator
from invenio_rdm_migrator.streams.transactions.drafts import (
    RDMDraftTransactionGenerator,
)


class ZenodoTransactionLoad(PostgreSQLExecute):
    """ZenodoRDM migrator transaction loading."""

    def __init__(self, db_uri, state, **kwargs):
        """Constructor."""
        parents_state = state["parents"]
        records_state = state["records"]
        communities_state = state["communities"]
        pids_state = state["pids"]
        table_tg_map = {
            "pidstore_pid": PIDRowGenerator(pids_state),
            "files_bucket": FilesBucketRowGenerator(),
            "records_metadata": [
                RDMDraftTransactionGenerator(
                    parents_state, records_state, communities_state, pids_state
                ),  # missing records
            ],
        }

        super().__init__(
            db_uri=db_uri,
            transaction_group_generator=TransactionGroupGenerator(table_tg_map),
            **kwargs,
        )
