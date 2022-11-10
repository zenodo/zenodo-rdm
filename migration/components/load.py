import uuid
from datetime import datetime
import random
import json
from invenio_records.dictutils import dict_set, dict_lookup
import psycopg
from psycopg.types.json import Jsonb
from schemas import DataSchema


def _generate_recid(data):
    return {
        "pk": random.randint(0, 2147483647 - 1),
        "obj_type": "rec",
        "pid_type": "recid",
        "status": "R",
    }


# NOTE: We need this to keep track of what Parent IDs we've already inserted in the
#       PIDs table.
SEEN_PARENT_IDS = set()


def _generate_uuid():
    return str(uuid.uuid4())


def jsonb(data):
    # return JsonB(data)
    return data


def now():
    return datetime.utcnow().isoformat()


class RecordLoad:

    PKS = [
        ("record.id", lambda _: _generate_uuid()),
        ("parent.id", lambda _: _generate_uuid()),
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

    REFS = [
        ("record.json.id", lambda x: x),
        ("parent.json.id", lambda x: x),
        ("record.json.pid.pk", lambda x: x),
        ("parent.json.pid.pk", lambda x: x),
        ("draft.id", lambda x: x),
    ]

    TABLE_MAP = {
        "parent": {
            "table": "rdm_parents_metadata",
            "cols": [
                "id",
                "json",
                "created",
                "updated",
                "version_id",
            ],
        },
        "record": {
            "table": "rdm_records_metadata",
            "cols": [
                "id",
                "json",
                "created",
                "updated",
                "version_id",
                "index",
                "bucket_id",
                "parent_id",
            ],
        },
        "record_files": {
            "table": "rdm_records_files",
            "cols": [
                "id",
                "json",
                "created",
                "updated",
                "version_id",
                "key",
                "record_id",
                "object_version_id",
            ],
        },
        "draft": {
            "table": "rdm_drafts_metadata",
            "cols": [
                "id",
                "json",
                "created",
                "updated",
                "version_id",
                "index",
                "bucket_id",
                "parent_id",
                "expires_at",
                "fork_version_id",
            ],
        },
        "draft_files": {
            "table": "rdm_records_files",
            "cols": [
                "id",
                "json",
                "created",
                "updated",
                "version_id",
                "key",
                "record_id",
                "object_version_id",
            ],
        },
        "version_state": {
            "table": "rdm_versions_state",
            "cols": [
                "latest_index",
                "parent_id",
                "latest_id",
                "next_draft_id",
            ],
        },
        "parents_community": {
            "table": "rdm_parents_community",
            "cols": [
                "community_id",
                "record_id",
                "request_id",
            ],
        },
        "pid": {
            "table": "pidstore_pid",
            "cols": [
                "id",
                "pid_type",
                "pid_value",
                "status",
                "object_type",
                "object_uuid",
                "created",
                "updated",
            ],
        },
    }

    def _validate(self, data):
        # TODO: JSONSchema + marshmallow?
        return DataSchema().validate(data)

    def _resolve_refs(self, data):
        # TODO: This is need only for updates (i.e. we lookup if something
        #       has already been inserted in the system).
        for path, resolve_func in self.REFS:
            try:
                value = dict_lookup(data, path)
                resolve_func(value, data)
            except KeyError:
                pass

    def _generate_pks(self, data):
        # TODO: Generating PKs also means we have to make sure the referenced
        #       models exist and are created as well (e.g. PIDs)
        for path, pk_func in self.PKS:
            dict_set(data, path, pk_func(data))

    def _copy(self, conn, table, tuples):
        table_cfg = self.TABLE_MAP[table]
        name = table_cfg["table"]
        cols = table_cfg["cols"]
        with conn.cursor() as cur:
            with cur.copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as copy:
                for row in tuples:
                    copy.write_row(row)
        conn.commit()

    def _generate_db_tuples(self, data):
        # Record
        rec = data["record"]
        pid = rec["json"]["pid"]
        yield (
            "record",
            (
                rec["id"],
                jsonb(rec["json"]),
                rec["created"],
                rec["updated"],
                rec["version_id"],
                rec["index"],
                rec.get("bucket_id"),
                rec["parent_id"],
            ),
        )
        # Recid
        yield (
            "pid",
            (
                pid["pk"],
                pid["pid_type"],
                rec["json"]["id"],
                pid["status"],
                pid["obj_type"],
                rec["id"],
                now(),
                now(),
            ),
        )
        # DOI
        if "doi" in rec["json"]["pids"]:
            yield (
                "pid",
                (
                    random.randint(0, 2147483647 - 1),
                    "doi",
                    rec["json"]["pids"]["doi"]["identifier"],
                    "R",
                    "rec",
                    rec["id"],
                    now(),
                    now(),
                ),
            )
        # OAI
        yield (
            "pid",
            (
                random.randint(0, 2147483647 - 1),
                "oai",
                rec["json"]["pids"]["oai"]["identifier"],
                "R",
                "rec",
                rec["id"],
                now(),
                now(),
            ),
        )
        # TODO: # Record files

        # TODO: # Draft
        # TODO: Draft files

        # Parent
        parent = data["parent"]
        if parent["json"]["id"] not in SEEN_PARENT_IDS:
            SEEN_PARENT_IDS.add(parent["json"]["id"])
            parent_pid = parent["json"]["pid"]
            yield (
                "parent",
                (
                    parent["id"],
                    jsonb(parent["json"]),
                    parent["created"],
                    parent["updated"],
                    parent["version_id"],
                ),
            )
            # Parent Recid
            yield (
                "pid",
                (
                    parent_pid["pk"],
                    parent_pid["pid_type"],
                    parent["json"]["id"],
                    parent_pid["status"],
                    parent_pid["obj_type"],
                    parent["id"],
                    now(),
                    now(),
                ),
            )
            # Version state
            yield (
                "version_state",
                (
                    rec["index"],
                    parent["id"],
                    rec["id"],
                    None,
                ),
            )

    def load(self, data):
        TABLE_ORDER = ["pid", "parent", "record", "version_state"]
        entries = {"record": [], "pid": [], "parent": [], "version_state": []}
        data = data["data"]
        self._validate(data)
        # TODO: We do this in case we want to make an update...
        # self._resolve_refs(d)
        self._generate_pks(data)
        for table, entry in self._generate_db_tuples(data):
            with open(f"migration/tables/{table}.jsonl", "w") as fp:
                fp.write(json.dumps(entry))
                fp.write("\n")
            entries[table].append(entry)
        # with psycopg.connect(
        #     "postgresql://zenodo:zenodo@localhost:5432/zenodo"
        # ) as conn:
        #     for table in TABLE_ORDER:
        #         self._copy(conn, table, entries[table])


class Load:

    STREAMS = {"record": RecordLoad, "user": None, "community": None}

    def __init__(self, stream):
        self.stream_loader = self.STREAMS[stream]

    def run(self, data):
        return self.stream_loader().load(data)
