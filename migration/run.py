import json
import sys
from nameparser import HumanName
import uuid
from pgcopy import CopyManager
import psycopg2
from invenio_records.dictutils import dict_set, dict_lookup


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
            pidstore_pid.object_type = 'rec'
        LIMIT 1
    ) as records
) TO STDOUT;
"""


class Extract:
    def run(self):
        # TODO: Run and yield from the query above somehow?
        # yield from engine.execute(EXTRACT_RECORDS_SQL)
        pass


class Transform:
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
        if data.get('doi'):
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
                "id": data["json"]["conceptrecid"],
                "pid": {
                    # TODO: Has to be generated in Load
                    # "pk": 15534,
                    "status": "R",
                    "obj_type": "rec",
                    "pid_type": "recid",
                },
                "access": {
                    "owned_by": [{"user": o} for o in data["json"].get("owners", [])]
                },
            },
        }
        comms = data.get("communities")
        if comms:
            r["communities"] = {
                "ids": [c for c in comms if c != "zenodo"],
                "default": comms[0],
            }
        return r

    def _record(self, data):

        return {
            "created": data["created"],
            "updated": data["updated"],
            "version_id": data["version_id"],
            "index": data.get("index", 0) + 1,  # in legacy we start at 0
            "json": {
                "id": str(data["json"]["recid"]),
                "pid": {
                    # TODO: Has to be generated in Load
                    # "pk": 15152,
                    "status": "R",
                    "obj_type": "rec",
                    "pid_type": "recid",
                },
                "pids": self._pids(data["json"]),
                "files": {"enabled": True},
                "metadata": self._metadata(data["json"]),
                "access": self._access(data["json"]),
            },
        }

    def _draft(self, data):
        return {}

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

    def run(self, data):
        return {
            "stream": "records",
            "id": self._id(data),
            "data": {
                "record": self._record(data),
                "draft": self._draft(data),
                "parent": self._parent(data),
                # TODO: we should actually have:
                # "record_files": ...
                # "draft_files": ...
                "files": self._files(data["json"].get("_files", [])),
            },
        }


class Load:

    PKS = [
        ("record.id", lambda _: str(uuid.uuid4())),
        ("record.id", lambda _: str(uuid.uuid4())),
        ("draft.id", lambda _: str(uuid.uuid4())),
        # TODO: Not sure if this is actually good. We should probably
        #       convert `pidstore_pid.id` to UUID
        ("record.json.pid.pk", lambda x: uuid.uuid4().int),
        ("parent.json.pid.pk", lambda x: uuid.uuid4().int),
        # TODO: We also need these:
        # ("record_files[].id", lambda _: str(uuid.uuid4())),
        # ("draft_files[].id", lambda _: str(uuid.uuid4())),
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
                "id", "json", "created", "updated", "version_id",
            ],
        },
        "record": {
            "table": "rdm_records_metadata",
            "cols": [
                "id", "json", "created", "updated", "version_id",
                "index", "bucket_id", "parent_id",
            ],
        },
        "record_files": {
            "table": "rdm_records_files",
            "cols": [
                "id", "json", "created", "updated", "version_id",
                "key", "record_id", "object_version_id",
            ],
        },
        "draft": {
            "table": "rdm_drafts_metadata",
            "cols": [
                "id", "json", "created", "updated", "version_id",
                "index", "bucket_id", "parent_id",
                "expires_at", "fork_verison_id",
            ],
        },
        "draft_files": {
            "table": "rdm_records_files",
            "cols": [
                "id", "json", "created", "updated", "version_id",
                "key", "record_id", "object_version_id",
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


    def _copy(self, data):
        records = [
                (0, 'Jerusalem', 72.2),
                (1, 'New York', 75.6),
                (2, 'Moscow', 54.3),
            ]
        conn = psycopg2.connect(database='weather_db')
        mgr = CopyManager(conn, 'measurements_table', cols)
        mgr.copy(records)
        conn.commit()

    def _generate_streams(self, data):
        pass

    def run(self, data):

        def _gen():
            for d in data:
                self._validate(d)
                # TODO: We do this in case we want to make an update...
                # self._resolve_refs(d)
                self._generate_pks(d)
                yield from self._generate_streams(d)

        for r in _gen():
            pass


if __name__ == "__main__":
    # Load().run()
    for l in sys.stdin.buffer:
        print(Transform().run(json.loads(l)))
