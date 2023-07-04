# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator funders loader."""

from invenio_rdm_migrator.load.postgresql.bulk import PostgreSQLCopyLoad
from invenio_rdm_migrator.load.postgresql.bulk.generators import (
    ExistingDataTableGenerator,
)
from invenio_rdm_migrator.streams.models.funders import Funders


class ZenodoFundersLoad(PostgreSQLCopyLoad):
    """Zenodo to RDM funders class for data loading."""

    def __init__(self, db_uri, data_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[
                ExistingDataTableGenerator(
                    tables=[Funders],
                    pks=[],
                )
            ],
            data_dir=data_dir,
            existing_data=True,
        )
