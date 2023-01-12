from datetime import datetime
from nameparser import HumanName

from invenio_rdm_migrator.streams.communities import (
    CommunityEntry,
    CommunityMemberEntry,
    CommunityTransform,
)
from invenio_rdm_migrator.streams.records import RDMRecordEntry, RDMRecordTransform
from invenio_rdm_migrator.streams.users import UserEntry, UserTransform


class ZenodoCommunityEntry(CommunityEntry):
    """Transform Zenodo community to RDM community."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return 1

    def _files(self, entry):
        """Transform the files of a record."""
        return {"enabled": True}

    def _slug(self, entry):
        """Returns the community slug."""
        return entry["id"]

    def _access(self, entry):
        """Returns community access."""
        return {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        }

    def _bucket_id(self, entry):
        """Returns the community bucket id."""
        return None

    def _metadata(self, entry):
        """Returns community metadata."""
        return {
            "page": entry["page"],
            "title": entry["title"],
            "curation_policy": entry["curation_policy"],
            "description": entry["description"],
        }


class ZenodoCommunityMemberEntry(CommunityMemberEntry):
    """Transform Zenodo community members to RDM community members."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return 1

    def _role(self, entry):
        """Returns the community member role."""
        return "owner"

    def _visible(self, entry):
        """Returns if the community member is visible or not."""
        return True

    def _active(self, entry):
        """Returns if the community member is active or not."""
        return True

    def _user_id(self, entry):
        """Returns the community member user id, if the member is a single user."""
        return entry["id_user"]

    def _group_id(self, entry):
        """Returns the community member group id, if the member is a group."""
        return None

    def _request_id(self, entry):
        """Returns the community member request id, if there is any request associated
        with the community member."""
        return None


class ZenodoCommunityTransform(CommunityTransform):
    """Zenodo to RDM Community class for data transformation."""

    def _community(self, entry):
        return ZenodoCommunityEntry().transform(entry)

    def _community_members(self, entry):
        """Transform the community members."""
        return [ZenodoCommunityMemberEntry().transform(entry)]


class ZenodoToRDMRecordEntry(RDMRecordEntry):
    """Transform Zenodo record to RDM record."""

    def _created(self, entry):
        """Returns the creation date of the record."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the record."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the record."""
        return entry["version_id"]

    def _index(self, entry):
        """Returns the index of the record."""
        return entry.get("index", 0) + 1  # in legacy we start at 0

    def _recid(self, entry):
        """Returns the recid of the record."""
        return str(entry["json"]["recid"])

    def _pids(self, entry):
        record = entry["json"]
        r = {
            "oai": {
                "provider": "oai",
                "identifier": record["_oai"]["id"],
            },
        }
        if record.get("doi"):
            r["doi"] = {
                "client": "datacite",
                "provider": "datacite",
                "identifier": record["doi"],
            }

        return r

    def _files(self, entry):
        """Transform the files of a record."""
        return {"enabled": True}

    def _access(self, entry):
        record = entry["json"]
        is_open = record["access_right"] == "open"
        r = {
            "record": "public",
            "files": "public" if is_open else "restricted",
        }
        if record["access_right"] == "embargoed":
            r["embargo"] = {
                "until": record["embargo_date"],
                "active": True,
            }
        return r

    def _metadata(self, entry):
        """Transform the metadata of a record."""

        def _creators(data):
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
                # autocompleted by RDM Metadata schema
                r["person_or_org"]["name"] = f"{name.surnames}, {name.first}"

                ret.append(r)
            return ret

        def _resource_type(data):
            t = data["type"]
            st = data.get("subtype")
            return {"id": f"{t}-{st}"} if st else {"id": t}

        record = entry["json"]
        r = {
            "title": record["title"],
            "description": record["description"],
            "publication_date": record["publication_date"],
            "resource_type": _resource_type(record["resource_type"]),
            "creators": _creators(record["creators"]),
        }

        return r


class ZenodoToRDMRecordTransform(RDMRecordTransform):
    """Zenodo to RDM Record class for data transformation."""

    def _community_id(self, entry):
        communities = entry["json"].get("communities")
        if communities:
            # TODO: handle all slugs
            slug = communities[0]
            if slug:
                return {"ids": [slug], "default": slug}
        return {}

    def _parent(self, entry):
        parent = {
            "created": entry["created"],  # same as the record
            "updated": entry["updated"],  # same as the record
            "version_id": entry["version_id"],
            "json": {
                # loader is responsible for creating/updating if the PID exists.
                "id": entry["json"]["conceptrecid"],
                "access": {
                    "owned_by": [{"user": o} for o in entry["json"].get("owners", [])]
                },
                "communities": self._community_id(entry),
            },
        }

        return parent

    def _record(self, entry):
        return ZenodoToRDMRecordEntry().transform(entry)

    def _draft(self, entry):
        return None

    def _draft_files(self, entry):
        return None

    def _record_files(self, entry):
        files = entry["json"].get("_files", [])
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
            for f in files
        ]


class ZenodoUserTransform(UserTransform):
    def _user(self, entry):
        """Transform the user."""
        return ZenodoUserEntry().transform(entry)

    def _session_activity(self, entry):
        """Transform the session activity."""
        return entry.get("session_activity")

    def _tokens(self, entry):
        """Transform the tokens."""
        return entry.get("tokens")

    def _applications(self, entry):
        """Transform the applications."""
        # TODO
        pass

    def _oauth(self, entry):
        """Transform the OAuth accounts."""
        # TODO
        pass

    def _identities(self, entry):
        """Transform the identities."""
        data = entry.get("identities")
        return [
            {
                "id": i["id"],
                "created": i["created"],
                "updated": i["updated"],
                "method": i["method"],
            }
            for i in data or []
        ]


class ZenodoUserEntry(UserEntry):
    """Transform a single user entry."""

    def _id(self, entry):
        """Returns the user ID."""
        return entry["id"]

    def _created(self, entry):
        """Returns the creation date."""
        return entry.get("created", datetime.utcnow().isoformat())

    def _updated(self, entry):
        """Returns the update date."""
        return entry.get("updated", datetime.utcnow().isoformat())

    def _version_id(self, entry):
        """Returns the version id."""
        return entry.get("version_id", 1)

    def _email(self, entry):
        """Returns the email."""
        return entry["email"]

    def _active(self, entry):
        """Returns if the user is active."""
        return entry["active"]

    def _password(self, entry):
        """Returns the password."""
        return entry.get("password")

    def _confirmed_at(self, entry):
        """Returns the confirmation date."""
        return entry.get("confirmed_at")

    def _username(self, entry):
        """Returns the username."""
        return entry.get("username")

    def _displayname(self, entry):
        """Returns the displayname."""
        return entry.get("displayname")

    def _profile(self, entry):
        """Returns the profile."""
        return {
            "full_name": entry.get("full_name"),
        }

    def _preferences(self, entry):
        """Returns the preferences."""
        return {
            "visibility": "restricted",
            "email_visibility": "restricted",
        }

    def _login_information(self, entry):
        """Returns the login information."""
        return {
            "last_login_at": entry.get("last_login_at"),
            "current_login_at": entry.get("current_login_at"),
            "last_login_ip": entry.get("last_login_ip"),
            "current_login_ip": entry.get("current_login_ip"),
            "login_count": entry.get("login_count"),
        }
