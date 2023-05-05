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


class ZenodoFilesTableGenerator(TableGenerator):
    """Zenodo to RDM table generator for files."""

    def __init__(self):
        """Constructor."""
        super().__init__(
            tables=[FilesInstance, FilesBucket, FilesObjectVersion],
            pks=[],
        )

    def _generate_rows(self, **kwargs):
        """Yield generated rows."""
        pass


class ZenodoFilesLoad(PostgreSQLCopyLoad):
    """Zenodo to RDM Files class for data loading."""

    def __init__(self, db_uri, tmp_dir, **kwargs):
        """Constructor."""
        super().__init__(
            db_uri=db_uri,
            table_generators=[ZenodoFilesTableGenerator()],
            tmp_dir=tmp_dir,
        )
        # override default as we don't generate the table files again
        self.tmp_dir = tmp_dir

    def _validate(self):
        """Validate data before loading."""
        return True

    def _prepare(self, entries):
        """Dump entries in csv files for COPY command."""
        files_table_generator = self.table_generators[0]
        return iter(files_table_generator.tables)
