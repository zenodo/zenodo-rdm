import contextlib
from copy import deepcopy
from dataclasses import fields
from datetime import datetime
from pathlib import Path

import psycopg
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.records.models import (
    RDMDraftMetadata,
    RDMParentMetadata,
    RDMRecordMetadata,
    RDMVersionsState,
)

from ..base import Load
from .tables import RDMRecordTableLoad, RDMVersionStateComputedTable


def _ts(iso=True):
    """Current timestamp string."""
    dt = datetime.now()
    return dt.isoformat() if iso else dt.timestamp()


class PostgreSQLCopyLoad(Load):
    """PostgreSQL COPY load."""

    def __init__(self, tables=None, computed_tables=None):
        """Constructor."""
        
        self.parent_cache = {}
        """
        used to keep track of what Parent IDs we've already inserted in the PIDs table.
        {
            '<parent_pid>': {
                'id': <generated_parent_uuid>,
                'version': {
                    'latest_index': 'record_index',
                    'latest_id': 'record id',
                }
        }
        """
        self.cur_dir = Path(__file__).parent
        self.output_dir = self.cur_dir / f"data/tables{_ts(iso=False)}"

        # tables to prepare from loaders
        self._tables = tables or [
            RDMRecordTableLoad(),
        ]

        _computed_tables = computed_tables or [
            RDMVersionStateComputedTable(self.parent_cache)
        ]
        self._tables.extend(_computed_tables)  # first tables, then computed ones

    def _cleanup_db(self):
        """Cleanup DB after load."""
        # TODO: abstract to tables
        # cant fix atm, versions state needs to be deleted in the middle
        PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type.in_(("recid", "doi", "oai")),
            PersistentIdentifier.object_type == "rec",
        ).delete()
        RDMVersionsState.query.delete()
        RDMRecordMetadata.query.delete()
        RDMParentMetadata.query.delete()
        RDMDraftMetadata.query.delete()
        db.session.commit()

    def _cleanup_files(self):
        """Cleanup files after load."""
        for table in self.stream_loader.TABLE_MAP["tables"].values():
            fpath = self.output_path / f"{table._table_name}.csv"
            print(f"Checking {fpath}")
            if fpath.exists():
                print(f"Deleting {fpath}")
                fpath.unlink(missing_ok=True)

    def _cleanup(self, db=False):
        """Cleanup csv files and DB after load."""
        self._cleanup_files()

        if db:  # DB cleanup is not always desired
            self._cleanup_db()

    def _prepare(self, datagen):
        """Dump entries in csv files for COPY command."""

        _prepared_tables = []
        for table in self._tables:
            # otherwise the generator is exahusted by the first table
            # TODO: nested generators, how expensive is this copy op?
            datagenc = deepcopy(datagen)
            _prepared_tables.append(
                table.prepare(self.output_dir, datagen=datagenc)
            )
        
        return iter(_prepared_tables)  # yield at the end vs yield per table

    def _load(self, tablegen):
        """Bulk load CSV table files.

        Loads the tables in the order given by the generator.
        """
        with psycopg.connect(
            "postgresql://zenodo:zenodo@localhost:5432/zenodo"
        ) as conn:
            for table in tablegen:
                name = table._table_name
                cols = ", ".join([f.name for f in fields(table)])
                fpath = self.output_path / f"{name}.csv"
                file_size = fpath.stat().st_size  # total file size for progress logging

                print(f"[{_ts()}] COPY FROM {fpath}")
                with contextlib.ExitStack() as stack:
                    cur = stack.enter_context(conn.cursor())
                    copy = stack.enter_context(
                        cur.copy(f"COPY {name} ({cols}) FROM STDIN (FORMAT csv)")
                    )
                    fp = stack.enter_context(open(fpath, "r"))

                    block_size = 8192

                    def _data_blocks(block_size=8192):
                        data = fp.read(block_size)
                        while data:
                            yield data
                            data = fp.read(block_size)

                    for idx, block in enumerate(_data_blocks(block_size)):
                        if idx % 100:
                            cur_bytes = idx * block_size
                            percentage = (cur_bytes / file_size) * 100
                            progress = f"{cur_bytes}/{file_size} ({percentage:.2f}%)"
                            print(f"[{_ts()}] {name}: {progress}")
                        copy.write(block)
                conn.commit()

    def run(self, datagen, cleanup=False):
        """Load entries"""
        tablegen = self._prepare(datagen) 
        self._load(tablegen)

        if cleanup:
            self._cleanup()
