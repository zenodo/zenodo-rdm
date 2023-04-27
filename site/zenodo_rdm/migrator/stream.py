# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Migrator stream definitions."""

import contextlib

from datetime import datetime
from pathlib import Path

from invenio_rdm_migrator.streams import StreamDefinition, Stream
from invenio_rdm_migrator.streams.communities import CommunityCopyLoad
from invenio_rdm_migrator.streams.files.models import (
    FilesBucket,
    FilesInstance,
    FilesObjectVersion,
)
from invenio_rdm_migrator.streams.records import RDMRecordCopyLoad
from invenio_rdm_migrator.streams.requests import RequestCopyLoad
from invenio_rdm_migrator.streams.users import UserCopyLoad

from .extract import JSONLExtract
from .transform import (
    ZenodoCommunityTransform,
    ZenodoFilesTransform,
    ZenodoRecordTransform,
    ZenodoRequestTransform,
    ZenodoUserTransform,
)

CommunitiesStreamDefinition = StreamDefinition(
    name="communities",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoCommunityTransform,
    load_cls=CommunityCopyLoad,
)
"""ETL stream for Zenodo to RDM communities."""

RecordStreamDefinition = StreamDefinition(
    name="records",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRecordTransform,
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo to RDM records."""

DraftStreamDefinition = StreamDefinition(
    name="drafts",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRecordTransform,
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo to RDM drafts."""

UserStreamDefinition = StreamDefinition(
    name="users",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoUserTransform,
    load_cls=UserCopyLoad,
)
"""ETL stream for Zenodo to import users."""

RequestStreamDefinition = StreamDefinition(
    name="requests",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRequestTransform,
    load_cls=RequestCopyLoad,
)
"""ETL stream for Zenodo to import users."""


# TODO: move this to a proper place or support custom stream classes
class FileStream(Stream):
    def __init__(self, db_uri, tmp_dir):
        """Constructor."""
        self.tmp_dir = tmp_dir
        self.db_uri = db_uri
        self.models = ["files_files", "files_bucket", "files_object"]
        self.model_map = {
            "files_files": FilesInstance,
            "files_bucket": FilesBucket,
            "files_object": FilesObjectVersion,
        }

    def _load(self):
        """Bulk load CSV table files.

        Loads the tables in the order given by the generator.
        """
        import psycopg

        def _ts(iso=True):
            """Current timestamp string."""
            dt = datetime.now()
            return dt.isoformat() if iso else dt.timestamp()

        def get_cols(model):
            from dataclasses import fields

            return ", ".join([f.name for f in fields(model)])

        with psycopg.connect(self.db_uri) as conn:
            for name in self.models:
                fpath = Path(self.tmp_dir) / f"{name}.csv"
                cols = get_cols(self.model_map[name])
                if fpath.exists():
                    # total file size for progress logging
                    file_size = fpath.stat().st_size

                    print(f"[{_ts()}] COPY FROM {fpath}")  # TODO: logging
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
                                progress = (
                                    f"{cur_bytes}/{file_size} ({percentage:.2f}%)"
                                )
                                print(f"[{_ts()}] {name}: {progress}")
                            copy.write(block)
                else:
                    # FIXME: log a WARNING/ERROR
                    print(f"[{_ts()}] {name}: no data to load")
                conn.commit()

    def run(self, cleanup=False):
        """Run ETL stream."""
        from datetime import datetime

        start_time = datetime.now()
        print(f"Stream started {start_time.isoformat()}")

        self._load()

        end_time = datetime.now()
        print(f"Stream ended {end_time.isoformat()}")

        print(f"Execution time: {end_time - start_time}")


"""ETL stream for Zenodo to import files."""
