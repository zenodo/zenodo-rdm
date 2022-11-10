import json
import uuid
import sys
from datetime import datetime
import random

from invenio_records.dictutils import dict_set, dict_lookup
import psycopg
from psycopg.types.json import Jsonb
from nameparser import HumanName


EXTRACT_RECORDS_SQL = """
COPY (
    SELECT row_to_json(records)
    FROM (
        SELECT
            r.*, pr.index
        FROM records_metadata as r
            JOIN pidstore_pid
                ON pidstore_pid.object_uuid = r.id
            JOIN pidrelations_pidrelation as pr
                ON pidstore_pid.id = pr.child_id
        WHERE
            pidstore_pid.pid_type = 'recid' AND
            pidstore_pid.status = 'R' AND
            pidstore_pid.object_type = 'rec' AND
            r.updated >= (:last_load_timestamp)
    ) as records
) TO STDOUT;
"""


class Extract:
    def run(self):
        # TODO: Run and yield from the query above somehow?
        # yield from engine.execute(EXTRACT_RECORDS_SQL)
        pass


class RecordTransform:
    def _creators(self, data):
        ret = []
        for c in data:
            r = {"person_or_org": {"type": "personal"}}
            if c.get("affiliation"):
                r["affiliations"] = [{"name": c["affiliation"]}]
            if c.get("orcid"):
                r["person_or_org"]["identifiers"] = [
                    {"scheme": "orcid", "identifier": c["orcid"]},
                ]
            name = HumanName(c["name"])
            r["person_or_org"]["given_name"] = name.first
            r["person_or_org"]["family_name"] = name.surnames

            ret.append(r)
        return ret

    def _resource_type(self, data):
        t = data["type"]
        st = data.get("subtype")
        return {"id": f"{t}-{st}"} if st else {"id": t}

    def _rights(self, data):
        license_id = data["$ref"].rsplit("/", 1)[-1].lower()
        # TODO: Map legacy license IDs (or create aliases in RDM)
        return [{"id": license_id}]

    def _metadata(self, data):
        r = {
            "title": data["title"],
            "description": data["description"],
            "publication_date": data["publication_date"],
            "resource_type": self._resource_type(data["resource_type"]),
            "creators": self._creators(data["creators"]),
        }
        if data.get("license"):
            r["rights"] = self._rights(data["license"])
        return r

    def _access(self, data):
        is_open = data["access_right"] == "open"
        r = {
            "record": "public",
            "files": "public" if is_open else "restricted",
        }
        if data["access_right"] == "embargoed":
            r["embargo"] = {
                "until": data["embargo_date"],
                "active": True,
            }
        return r

    def _pids(self, data):
        r = {
            "oai": {
                "provider": "oai",
                "identifier": data["_oai"]["id"],
            },
        }
        if data.get("doi"):
            r["doi"] = {
                "client": "datacite",
                "provider": "datacite",
                "identifier": data["doi"],
            }
        return r

    def _parent(self, data):
        r = {
            # NOTE: Copy from record
            "created": data["created"],
            "updated": data["updated"],
            "version_id": data["version_id"],
            "json": {
                # TODO: Loader is responsible for creating/updating if the PID exists.
                "id": data["json"]["conceptrecid"],
                "access": {
                    "owned_by": [{"user": o} for o in data["json"].get("owners", [])]
                    # TODO: See how we migrate restricted access links. This is
                    #       different in legacy, where we track links per record version
                    #       and not on the parent-level.
                },
            },
        }
        # TODO: Enable communities after handling "communities" stream, because we will
        #       need their PK for inserting entries in `rdm_`
        # comms = data.get("communities")
        # if comms:
        #     r["communities"] = {
        #         "ids": [c for c in comms if c != "zenodo"],
        #         "default": comms[0],
        #     }
        return r

    def _record(self, data):

        return {
            "created": data["created"],
            "updated": data["updated"],
            "version_id": data["version_id"],
            "index": data.get("index", 0) + 1,  # in legacy we start at 0
            "json": {
                "id": str(data["json"]["recid"]),
                "pids": self._pids(data["json"]),
                "files": {"enabled": True},
                "metadata": self._metadata(data["json"]),
                "access": self._access(data["json"]),
            },
        }

    def _draft(self, data):
        return None

    def _files(self, data):
        return [
            {
                "key": f["key"],
                "object_version": {
                    "file": {
                        "size": f["size"],
                        "checksum": f["checksum"],
                    },
                },
            }
            for f in data
        ]

    def _id(self, data):
        recid = str(data["json"]["recid"])
        record_revision_id = data["version_id"]
        draft_revision_id = None
        return (recid, record_revision_id, draft_revision_id)

    def transform(self, data):
        return {
            "stream": "records",
            "id": self._id(data),  # unique stream id used for check a stream status
            "data": {
                "record": self._record(data),
                "draft": self._draft(data),
                "parent": self._parent(data),
                # TODO: we should actually have:
                "record_files": self._files(data["json"].get("_files", [])),
                # "draft_files": ...
            },
        }


class Transform:

    STREAMS = {"record": RecordTransform, "user": None, "community": None}

    def __init__(self, stream):
        self.stream_transformer = self.STREAMS[stream]

    def run(self, data):
        return self.stream_transformer().transform(data)


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

class RecordLoad:

    PKS = [
        ("record.id", lambda _: uuid.uuid4()),
        ("parent.id", lambda _: uuid.uuid4()),
        # ("draft.id", lambda _: uuid.uuid4()),
        # TODO: Not sure if this is actually good. We should probably
        #       convert `pidstore_pid.id` to UUID
        ("record.json.pid", _generate_recid),
        ("parent.json.pid", _generate_recid),
        # TODO: We also need these:
        # ("record_files[].id", lambda _: uuid.uuid4()),
        # ("draft_files[].id", lambda _: uuid.uuid4()),
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
        return True

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
        now = datetime.utcnow()
        # Record
        rec = data["record"]
        pid = rec["json"]["pid"]
        yield (
            "record",
            (
                rec["id"],
                Jsonb(rec["json"]),
                rec["created"],
                rec["updated"],
                rec["version_id"],
                rec["index"],
                rec.get("bucket_id"),
                rec["parent_id"],
            )
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
                now,
                now,
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
                    now,
                    now,
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
                now,
                now,
            ),
        )
        # TODO: # Record files

        # TODO: # Draft
        # TODO: Draft files

        # Parent
        parent = data["parent"]
        parent_pid = parent["json"]["pid"]
        yield (
            "parent",
            (
                parent["id"],
                Jsonb(parent["json"]),
                parent["created"],
                parent["updated"],
                parent["version_id"],
            )
        )
        # Parent Recid
        if parent["json"]["id"] not in SEEN_PARENT_IDS:
            SEEN_PARENT_IDS.add(parent["json"]["id"])
            yield (
                "pid",
                (
                    parent_pid["pk"],
                    parent_pid["pid_type"],
                    parent["json"]["id"],
                    parent_pid["status"],
                    parent_pid["obj_type"],
                    parent["id"],
                    now,
                    now,
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
            # with open(f"{table}.jsonl", "a") as fp:
            #     fp.write(json.dumps(entry))
            #     fp.write("\n")
            entries[table].append(entry)
        with psycopg.connect("postgresql://zenodo:zenodo@localhost:5432/zenodo") as conn:
            for table in TABLE_ORDER:
                self._copy(conn, table, entries[table])


class Load:

    STREAMS = {"record": RecordLoad, "user": None, "community": None}

    def __init__(self, stream):
        self.stream_loader = self.STREAMS[stream]

    def run(self, data):
        return self.stream_loader().load(data)


# NOTE: Usage
#   gzip -dc records-dump-2022-11-08.jsonl.gz | head | sed 's/\\\\/\\/g' | python migration/run.py

if __name__ == "__main__":
    for idx, l in enumerate(sys.stdin.buffer):
        if idx % 100 == 0:
            print(datetime.now().isoformat(), idx)
        record_transform = Transform(stream="record")
        record_load = Load(stream="record")
        transform_result = record_transform.run(json.loads(l))

    # Write everything now:

    record_load.run(transform_result)
