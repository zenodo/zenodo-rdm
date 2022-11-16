import contextlib
import csv
import json
import psycopg
import random
import uuid
from dataclasses import dataclass, InitVar, fields
from datetime import datetime
from invenio_records.dictutils import dict_set
from pathlib import Path

# from schemas import DataSchema


# Keep track of generated PKs, since there's a chance they collide
GENERATED_PID_PKS = set()


def _pid_pk():
    while True:
        # We start at 1M to avoid collisions with existing low-numbered PKs
        val = random.randint(1_000_000, 2_147_483_647 - 1)
        if val not in GENERATED_PID_PKS:
            GENERATED_PID_PKS.add(val)
            return val


def _ts():
    """Current timestamp string."""
    return datetime.now().isoformat()


def _generate_recid(data):
    return {
        "pk": _pid_pk(),
        "obj_type": "rec",
        "pid_type": "recid",
        "status": "R",
    }


def _generate_uuid(data):
    return str(uuid.uuid4())


def as_csv_row(dc):
    """Serialize a dataclass instance as a CSV-writable row."""
    row = []
    for f in fields(dc):
        val = getattr(dc, f.name)
        if val:
            if issubclass(f.type, (dict,)):
                val = json.dumps(val)
            elif issubclass(f.type, (datetime,)):
                val = val.isoformat()
            elif issubclass(f.type, (uuid.UUID,)):
                val = str(val)
        row.append(val)
    return row


#
# Dataclasses for generating table rows
#
@dataclass
class PersistentIdentifier:

    id: str
    pid_type: str
    pid_value: str
    status: str
    object_type: str
    object_uuid: str
    created: str
    updated: str

    _table_name: InitVar[str] = "pidstore_pid"


@dataclass
class RDMRecordMetadata:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int
    index: int
    bucket_id: str
    parent_id: str

    _table_name: InitVar[str] = "rdm_records_metadata"


@dataclass
class RDMRecordFile:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int
    key: str
    record_id: str
    object_version_id: str

    _table_name: InitVar[str] = "rdm_records_files"


@dataclass
class RDMParentMetadata:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int

    _table_name: InitVar[str] = "rdm_parents_metadata"


@dataclass
class RDMVersionState:

    latest_index: int
    parent_id: str
    latest_id: str
    next_draft_id: str

    _table_name: InitVar[str] = "rdm_versions_state"


@dataclass
class RDMDraftMetadata:

    id: str
    json: dict
    created: str
    updated: str
    version_id: int
    index: int
    bucket_id: str
    parent_id: str

    expires_at: str
    fork_version_id: int

    _table_name: InitVar[str] = "rdm_drafts_metadata"


@dataclass
class RDMDraftFile(RDMRecordFile):

    _table_name: InitVar[str] = "rdm_drafts_files"


@dataclass
class RDMParentCommunity:

    community_id: str
    record_id: str
    request_id: str

    _table_name: InitVar[str] = "rdm_parents_community"


class RecordLoad:
    def __init__(self, table_map, is_db_empty, parent_cache, output_path):
        self.TABLE_MAP = table_map
        self.is_db_empty = is_db_empty
        self.parent_cache = parent_cache
        self.output_path = Path(output_path)

    PKS = [
        ("record.id", _generate_uuid),
        ("parent.id", _generate_uuid),
        # ("draft.id", lambda _: _generate_uuid()),
        # TODO: Not sure if this is actually good. We should probably
        #       convert `pidstore_pid.id` to UUID
        ("record.json.pid", _generate_recid),
        ("parent.json.pid", _generate_recid),
        # TODO: We also need these:
        # ("record_files[].id", lambda _: _generate_uuid()),
        # ("draft_files[].id", lambda _: _generate_uuid()),
        ("record.parent_id", lambda d: d["parent"]["id"]),
        # Record
        # ("record.bucket_id", lambda x: x),
        # Draft
        # ("draft.parent_id", lambda d: d["parent"]["id"]),
        # ("draft.bucket_id", lambda x: x),
    ]

    # REFS = [
    #     ("record.json.id", lambda x: x),
    #     ("parent.json.id", lambda x: x),
    #     ("record.json.pid.pk", lambda x: x),
    #     ("parent.json.pid.pk", lambda x: x),
    #     ("draft.id", lambda x: x),
    # ]

    def _validate(self, data):
        # TODO: JSONSchema + marshmallow?
        # return DataSchema().validate(data)
        return True

    # def _resolve_refs(self, data):
    #     # TODO: This is need only for updates (i.e. we lookup if something
    #     #       has already been inserted in the system).
    #     for path, resolve_func in self.REFS:
    #         try:
    #             value = dict_lookup(data, path)
    #             resolve_func(value, data)
    #         except KeyError:
    #             pass

    def _generate_pks(self, data):
        # TODO: Generating PKs also means we have to make sure the referenced
        #       models exist and are created as well (e.g. PIDs)
        for path, pk_func in self.PKS:
            dict_set(data, path, pk_func(data))

    def _generate_db_tuples(self, data):
        now = datetime.utcnow().isoformat()

        # Record
        rec = data["record"]
        record_pid = rec["json"]["pid"]
        parent = data["parent"]
        rec_parent_id = self.parent_cache.get(parent["json"]["id"], {}).get("id")
        yield RDMRecordMetadata(
            id=rec["id"],
            json=rec["json"],
            created=rec["created"],
            updated=rec["updated"],
            version_id=rec["version_id"],
            index=rec["index"],
            bucket_id=rec.get("bucket_id"),
            parent_id=rec_parent_id or rec["parent_id"],
        )
        # Recid
        yield PersistentIdentifier(
            id=record_pid["pk"],
            pid_type=record_pid["pid_type"],
            pid_value=rec["json"]["id"],
            status=record_pid["status"],
            object_type=record_pid["obj_type"],
            object_uuid=rec["id"],
            created=now,
            updated=now,
        )
        # DOI
        if "doi" in rec["json"]["pids"]:
            yield PersistentIdentifier(
                id=_pid_pk(),
                pid_type="doi",
                pid_value=rec["json"]["pids"]["doi"]["identifier"],
                status="R",
                object_type="rec",
                object_uuid=rec["id"],
                created=now,
                updated=now,
            )
        # OAI
        yield PersistentIdentifier(
            id=_pid_pk(),
            pid_type="oai",
            pid_value=rec["json"]["pids"]["oai"]["identifier"],
            status="R",
            object_type="rec",
            object_uuid=rec["id"],
            created=now,
            updated=now,
        )
        # TODO: Record files

        # TODO: Draft
        # TODO: Draft files

        # Parent
        if parent["json"]["id"] not in self.parent_cache:
            self.parent_cache[parent["json"]["id"]] = dict(
                id=parent["id"],
                version=dict(latest_index=rec["index"], latest_id=rec["id"]),
            )
            parent_pid = parent["json"]["pid"]
            yield RDMParentMetadata(
                id=parent["id"],
                json=parent["json"],
                created=parent["created"],
                updated=parent["updated"],
                version_id=parent["version_id"],
            )
            # Parent Recid
            yield PersistentIdentifier(
                id=parent_pid["pk"],
                pid_type=parent_pid["pid_type"],
                pid_value=parent["json"]["id"],
                status=parent_pid["status"],
                object_type=parent_pid["obj_type"],
                object_uuid=parent["id"],
                created=now,
                updated=now,
            )
        else:
            # parent in cache - update version
            cached_parent = self.parent_cache[parent["json"]["id"]]
            # check if current record is a new version of the cached one
            if cached_parent["version"]["latest_index"] < rec["index"]:
                cached_parent["version"] = dict(
                    latest_index=rec["index"], latest_id=rec["id"]
                )

    def prepare_load(self, data):
        """Append to CSV table files."""
        data = data["data"]
        self._validate(data)
        if self.is_db_empty:
            # TODO: We do this in case we want to make an update...
            # self._resolve_refs(d)
            self._generate_pks(data)

        # NOTE: use this context manager to close all opened files at once
        with contextlib.ExitStack() as stack:
            out_files = {}

            for entry in self._generate_db_tuples(data):
                if entry._table_name not in out_files:
                    fpath = self.output_path / f"{entry._table_name}.csv"
                    out_files[entry._table_name] = csv.writer(
                        stack.enter_context(open(fpath, "a"))
                    )
                writer = out_files[entry._table_name]
                writer.writerow(as_csv_row(entry))

    def load(self):
        """Bulk load CSV table files."""
        with psycopg.connect(
            # TODO: Parametrize this
            "postgresql://zenodo:zenodo@localhost:5432/zenodo"
        ) as conn:
            for table in self.TABLE_MAP["order"]:
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

    def load_rdm_versions_state(self):
        """Append version state table."""

        def _generate_db_tuples():
            for parent_id, parent_state in self.parent_cache.items():
                # Version state to be populated in the end from the final state
                yield RDMVersionState(
                    latest_index=parent_state["version"]["latest_index"],
                    parent_id=parent_state["id"],
                    latest_id=parent_state["version"]["latest_id"],
                    next_draft_id=None,
                )

        fpath = self.output_path / f"rdm_versions_state.csv"
        with open(fpath, "a") as fp:
            writer = csv.writer(fp)
            for entry in _generate_db_tuples():
                writer.writerow(as_csv_row(entry))

    def load_computed_tables(self):
        """Load computed tables for 'record' stream."""
        computed_tables = self.TABLE_MAP["computed_tables"]
        for table in computed_tables:
            load_table = getattr(self, f"load_{table._table_name}")
            if load_table:
                load_table()


class Load:

    STREAMS = {"record": RecordLoad, "user": None, "community": None}
    TABLE_MAP = {
        "record": {
            "tables": {
                "parent": RDMParentMetadata,
                "record": RDMRecordMetadata,
                # "record_files": RDMRecordFile,
                # "draft": RDMDraftMetadata,
                # "draft_files": RDMDraftFile,
                "version_state": RDMVersionState,
                # "parents_community": RDMParentCommunity,
                "pid": PersistentIdentifier,
            },
            "order": [
                PersistentIdentifier,
                RDMParentMetadata,
                RDMRecordMetadata,
                # RDMRecordFile,
                # RDMDraftMetadata,
                # RDMDraftFile,
                # RDMParentCommunity,
                RDMVersionState,
            ],
            # tables that are populated in the end from the existing DB state
            "computed_tables": [RDMVersionState],
        }
    }

    def __init__(self, stream, parent_cache, output_path):
        self.stream = stream
        self._stream_loader_cls = self.STREAMS[stream]
        self.parent_cache = parent_cache
        self.output_path = output_path

    @property
    def stream_loader(self):
        return self._stream_loader_cls(
            self.TABLE_MAP[self.stream],
            is_db_empty=True,
            # is_db_empty=self.is_db_empty(),
            parent_cache=self.parent_cache,
            output_path=self.output_path,
        )

    def is_db_empty(self):
        """Returns if db for the specified stream is empty."""
        with psycopg.connect(
            "postgresql://zenodo:zenodo@localhost:5432/zenodo"
        ) as conn, conn.cursor() as cur:
            # NOTE: Not entirely correct, since e.g. for PIDs, we would still have
            #       entries for vocabularies.
            tables = self.TABLE_MAP[self.stream]["tables"]
            for table_id, table in tables.items():
                cur.execute(f"SELECT count(*) from {table._table_name};")
            (total_rows,) = cur.fetchone()
            return False if total_rows else True

    def reset_load(self):
        for table in self.stream_loader.TABLE_MAP["tables"].values():
            fpath = self.output_path / f"{table._table_name}.csv"
            print(f"Checking {fpath}")
            if fpath.exists():
                print(f"Deleting {fpath}")
                fpath.unlink(missing_ok=True)

    def prepare_load(self, data):
        return self.stream_loader.prepare_load(data)

    def load_computed_tables(self):
        return self.stream_loader.load_computed_tables()

    def load(self):
        return self.stream_loader.load()
