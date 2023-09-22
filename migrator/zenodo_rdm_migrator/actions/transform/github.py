# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration github actions module."""

import orjson
from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load
from invenio_rdm_migrator.streams.github import GitHubRepositoryTransform
from invenio_rdm_migrator.streams.oauth import OAuthServerTokenTransform
from invenio_rdm_migrator.transform import IdentityTransform, JSONTransformMixin

from ...transform.entries.parents import ParentRecordEntry
from ...transform.entries.records.records import ZenodoRecordEntry

#
# Hooks
#


class HookRepoUpdateAction(TransformAction):
    """Zenodo to RDM GitHub repository update of a webhook.

    This will serve for hook enabling first phase and for disabling, as well as for
    normal repository updates.
    """

    name = "gh-hook-repo-update"
    load_cls = load.HookRepoUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "github_repositories"
            and op["op"] == OperationType.UPDATE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        self._microseconds_to_isodate(data=op["after"], fields=["created", "updated"])

        result = {
            "tx_id": self.tx.id,
            "gh_repository": GitHubRepositoryTransform()._transform(op["after"]),
        }

        return result


class HookEventCreateAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM webhook create action.

    This will serve for hook enabling first phase and for disabling, as well as for
    normal repository updates.
    """

    name = "gh-hook-event-create"
    load_cls = load.HookEventCreateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) == 1:
            op = tx.operations[0]
            return (
                op["source"]["table"] == "webhooks_events"
                and op["op"] == OperationType.INSERT
            )

        if len(tx.operations) == 2:
            rules = {
                "webhooks_events": OperationType.INSERT,
                "oauth2server_token": OperationType.UPDATE,
            }

            for op in tx.operations:
                rule = rules.pop(op["source"]["table"], None)
                if not rule or rule != op["op"]:
                    return False

            return True

        return False

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        webhook_event = None
        server_token = None
        for op in self.tx.operations:
            if op["source"]["table"] == "webhooks_events":
                self._microseconds_to_isodate(
                    data=op["after"], fields=["created", "updated"]
                )
                self._load_json_fields(
                    data=op["after"],
                    fields=[
                        "payload",
                        "payload_headers",
                        "response",
                        "response_headers",
                    ],
                )
                webhook_event = op["after"]
            elif op["source"]["table"] == "oauth2server_token":
                self._microseconds_to_isodate(data=op["after"], fields=["expires"])
                server_token = op["after"]

        result = {
            "tx_id": self.tx.id,
            "webhook_event": IdentityTransform()._transform(webhook_event),
        }
        if server_token:
            result["oauth_token"] = OAuthServerTokenTransform()._transform(server_token)

        return result


class HookEventUpdateAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM webhook event update."""

    name = "gh-hook-event-update"
    load_cls = load.HookEventUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "webhooks_events"
            and op["op"] == OperationType.UPDATE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        self._load_json_fields(
            data=op["after"],
            fields=["payload", "payload_headers", "response", "response_headers"],
        )
        self._microseconds_to_isodate(data=op["after"], fields=["created", "updated"])

        result = {
            "tx_id": self.tx.id,
            "webhook_event": IdentityTransform()._transform(op["after"]),
        }

        return result


#
# Releases
#


class ReleaseReceiveAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM receive/create a GitHub release action."""

    name = "gh-release-receive"
    load_cls = load.ReleaseReceiveAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 2:
            return False

        rules = {
            "github_repositories": OperationType.UPDATE,
            "github_releases": OperationType.INSERT,
        }

        for op in tx.operations:
            rule = rules.pop(op["source"]["table"], None)
            if not rule or rule != op["op"]:
                return False

        return True

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        repo = None
        release = None
        for op in self.tx.operations:
            self._microseconds_to_isodate(
                data=op["after"], fields=["created", "updated"]
            )
            if op["source"]["table"] == "github_repositories":
                repo = op["after"]
            elif op["source"]["table"] == "github_releases":
                release = op["after"]
                self._load_json_fields(data=release, fields=["errors"])

        return {
            "tx_id": self.tx.id,
            "gh_repository": GitHubRepositoryTransform()._transform(repo),
            # using identity because it accounts for partial updates
            "gh_release": IdentityTransform()._transform(release),
        }


class ReleaseUpdateAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM update a GitHub release action."""

    name = "gh-release-update"
    load_cls = load.ReleaseUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        if len(tx.operations) != 1:
            return False

        op = tx.operations[0]

        return (
            op["source"]["table"] == "github_releases"
            and op["op"] == OperationType.UPDATE
        )

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        op = self.tx.operations[0]

        self._load_json_fields(data=op["after"], fields=["errors"])
        self._microseconds_to_isodate(data=op["after"], fields=["created", "updated"])

        return {
            "tx_id": self.tx.id,
            # using identity because it accounts for partial updates
            "gh_release": IdentityTransform()._transform(op["after"]),
        }


class ReleaseProcessAction(TransformAction, JSONTransformMixin):
    """Zenodo to RDM process a GitHub release action."""

    name = "gh-release-process"
    load_cls = load.ReleaseProcessAction

    @staticmethod
    def _patch_data(original, patch):
        for key, value in patch.items():
            original[key] = value

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        rules = {
            "records_metadata",
            "pidstore_pid",
            "files_bucket",
            "files_object",
            "files_files",
            "github_releases",
        }

        for op in tx.operations:
            if op["source"]["table"] in rules and op["op"] == OperationType.INSERT:
                rules.remove(op["source"]["table"])

        # there is at least one creation of each of the tables needed
        return len(rules) == 0

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        # the logic behind having dictionaries is that there are many rows of the same
        # table (e.g record and deposit bucket, many pids), and they cannot be discarded
        # until the record metadata is final and complete. then for example we can discard
        # the deposit bucket, however, until that point we had to patch the updates on all
        # rows.
        records = {}
        pids = {}
        dois = {}
        buckets = {}
        fos = {}  # file objects

        record_oai = None
        release = None

        for op in self.tx.operations:
            table = op["source"]["table"]
            if table == "pidstore_pid":
                if op["before"] == None:  # create
                    # ignore depid
                    if op["after"]["pid_type"] == "doi":
                        dois[op["after"]["object_uuid"]] = op["after"]
                    elif op["after"]["pid_type"] == "oai":
                        record_oai = op["after"]
                    elif op["after"]["pid_type"] == "recid":
                        # add pids then find which is which once the rec meta is processed
                        # there might be more than two, but excluded by the rec meta
                        pids[op["after"]["id"]] = op["after"]
                else:  # updates only to recids (not asserted in the code though)
                    recid = op["after"]["id"]
                    # not pid -> e.g. when the parent already exists
                    pid = pids.get(recid)
                    pids[recid] = (
                        self._patch_data(pid, op["after"]) if pid else op["after"]
                    )

            elif table == "files_bucket":
                # should be only two, deposit and record
                bucket_id = op["after"]["id"]
                bucket = buckets.get(bucket_id)
                buckets[bucket_id] = (
                    self._patch_data(bucket, op["after"]) if bucket else op["after"]
                )

            elif table == "files_object":
                # should be only two, deposit and record
                bucket_id = op["after"]["bucket_id"]
                fo = fos.get(bucket_id)
                fos[bucket_id] = (
                    self._patch_data(fo, op["after"]) if fo else op["after"]
                )

            elif table == "files_files":
                # there is only one, both fo point to it
                fi = self._patch_data(fi, op["after"]) if fi else op["after"]

            elif table == "records_metadata":
                # there are two created: record and deposit
                # updates to other records are discarded
                # deposit is discarded after transformation
                if op["before"] == None:  # create
                    records[op["after"]["id"]] = op["after"]
                else:
                    records[op["after"]["id"]] = self._patch_data(
                        records[op["after"]["id"]], op["after"]
                    )

            elif table == "github_releases":
                if not release:
                    release = op["after"]
                else:
                    self._patch_data(release, op["after"])

            else:
                if table not in {"pidstore_redirect", "pidrelations_pidrelation"}:
                    # ignoring a table that was not considered, might be a bug
                    raise

        # transform records and discard deposit
        record = None
        for _, rec_meta in records.items():
            rec_meta["json"] = orjson.loads(rec_meta["json"])
            if not "deposits" in rec_meta["json"]["$schema"]:
                # this code assumes there is only one record and one deposit
                record = rec_meta

        record = ZenodoRecordEntry(partial=True).transform(rec_meta)
        parent = ParentRecordEntry(partial=True).transform(record)
        # communities should not be needed to clear since the GH releases
        # don't belong to one
        # parent["json"]["communities"] = {}

        # choose pid and parent pid based on record metadata
        record_pid = pids[record["json"]["id"]]
        try:
            parent_pid = pids[parent["json"]["id"]]
        except KeyError:
            # if not present it was already registered in a previous release
            pass

        # calculate parent doi
        record_doi = dois[record["id"]]
        try:
            parent_doi = dois[parent["id"]]
        except KeyError:
            # if not present it was already registered in a previous release
            pass

        # choose the bucket according to the record bucket_id
        bucket = buckets[record["bucket_id"]]
        fo = fos[bucket["id"]]  # file object

        # calculate file record
        fr = {
            "id": None,  # generated by the load action
            "json": {},
            "created": fo["created"],
            "updated": fo["updated"],
            "version_id": 1,
            "key": fo["key"],
            "record_id": None,  # calculated by the load action
            "object_version_id": fo["version_id"],
        }

        # load json fields
        self._load_json_fields(data=release, fields=["errors"])

        # transform datetime fields
        self._microseconds_to_isodate(data=record_pid, fields=["created", "updated"])
        self._microseconds_to_isodate(data=record_doi, fields=["created", "updated"])
        self._microseconds_to_isodate(data=record_oai, fields=["created", "updated"])
        self._microseconds_to_isodate(data=bucket, fields=["created", "updated"])
        self._microseconds_to_isodate(data=fo, fields=["created", "updated"])
        self._microseconds_to_isodate(
            data=fi, fields=["created", "updated", "last_checked_at"]
        )
        self._microseconds_to_isodate(
            data=record, fields=["created", "updated", "expires_at"]
        )
        self._microseconds_to_isodate(data=parent, fields=["created", "updated"])
        self._microseconds_to_isodate(data=release, fields=["created", "updated"])

        # TODO: the load action needs to store the pids in state because the parent
        # could be in the first release and this be the second, need to find it

        # note: record and parent need to be transformed (done in lines above)
        # the rest are simple "identity" and since we already have a dict they can be
        # passed as they are
        result = {
            "tx_id": self.tx.id,
            "record_pid": record_pid,
            "record_doi": record_doi,
            "record_oai": record_oai,
            "file_bucket": bucket,
            "file_object": fo,
            "file_instance": fi,
            "file_record": fr,
            "parent": record,
            "record": parent,
            # using identity because it accounts for partial updates
            "gh_release": release,
        }

        if parent_pid:
            self._microseconds_to_isodate(
                data=parent_pid, fields=["created", "updated"]
            )
            result["parent_pid"] = parent_pid

        if parent_doi:
            self._microseconds_to_isodate(
                data=parent_doi, fields=["created", "updated"]
            )
            result["parent_doi"] = parent_doi

        return result
