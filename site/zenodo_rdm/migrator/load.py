# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator files loader."""

from invenio_rdm_migrator.load.postgresql import (
    ExistingDataTableGenerator,
    PostgreSQLCopyLoad,
)
from invenio_rdm_migrator.streams.files.models import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)

from invenio_rdm_migrator.streams.models import Awards, Funders


class ZenodoFilesLoad(PostgreSQLCopyLoad):
    """Zenodo to RDM Files class for data loading."""

    def __init__(self, db_uri, data_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[
                ExistingDataTableGenerator(
                    tables=[FilesInstance, FilesBucket, FilesObjectVersion], pks=[]
                )
            ],
            data_dir=data_dir,
            existing_data=True,
        )


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


class ZenodoAwardsLoad(PostgreSQLCopyLoad):
    """Zenodo to RDM awards class for data loading."""

    def __init__(self, db_uri, data_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[
                ExistingDataTableGenerator(
                    tables=[Awards],
                    pks=[],
                )
            ],
            data_dir=data_dir,
            existing_data=True,
        )
