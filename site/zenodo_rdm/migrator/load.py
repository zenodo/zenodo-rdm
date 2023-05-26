# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator files loader."""

from invenio_rdm_migrator.load.postgresql import PostgreSQLCopyLoad, TableGenerator
from invenio_rdm_migrator.streams.files.models import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)

from .models import Awards, Funders


class ZenodoExistingDataTableGenaratorBase(TableGenerator):
    """Zenodo to RDM table generator for directly loaded data streams."""

    def _generate_rows(self, **kwargs):
        """Yield generated rows."""
        pass


class ZenodoExistingDataLoadBase(PostgreSQLCopyLoad):
    """Zenodo to RDM load class for direct data loading."""

    def _validate(self):
        """Validate data before loading."""
        return True


class ZenodoFilesLoad(ZenodoExistingDataLoadBase):
    """Zenodo to RDM Files class for data loading."""

    def __init__(self, db_uri, data_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[
                ZenodoExistingDataTableGenaratorBase(
                    tables=[FilesInstance, FilesBucket, FilesObjectVersion], pks=[]
                )
            ],
            data_dir=data_dir,
            existing_data=True,
        )


class ZenodoFundersLoad(ZenodoExistingDataLoadBase):
    """Zenodo to RDM funders class for data loading."""

    def __init__(self, db_uri, data_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[
                ZenodoExistingDataTableGenaratorBase(
                    tables=[Funders],
                    pks=[],
                )
            ],
            data_dir=data_dir,
            existing_data=True,
        )


class ZenodoAwardsLoad(ZenodoExistingDataLoadBase):
    """Zenodo to RDM awards class for data loading."""

    def __init__(self, db_uri, data_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[
                ZenodoExistingDataTableGenaratorBase(
                    tables=[Awards],
                    pks=[],
                )
            ],
            data_dir=data_dir,
            existing_data=True,
        )
