from nameparser import HumanName
from schemas import RecordStreamSchema


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

        # TODO: check if license exists or create as custom
        # if data.get("license"):
        #     r["rights"] = self._rights(data["license"])
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
            "stream": "record",
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
        result = self.stream_transformer().transform(data)
        # the payload is validated in the Loader
        # maybe here is a nice-to-have for avoiding surprises
        RecordStreamSchema().validate(result)
        return result
