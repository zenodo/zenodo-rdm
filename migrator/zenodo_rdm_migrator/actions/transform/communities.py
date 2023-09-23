# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio RDM migration community actions module."""

from invenio_rdm_migrator.actions import TransformAction
from invenio_rdm_migrator.load.postgresql.transactions.operations import OperationType
from invenio_rdm_migrator.streams.actions import load

from ...transform.entries.communities import (
    ZenodoCommunityEntry,
    ZenodoCommunityFileEntry,
    ZenodoCommunityFilesBucketEntry,
    ZenodoCommunityMemberEntry,
)


class CommunityCreateAction(TransformAction):
    """Zenodo to RDM community create action."""

    name = "community-create"
    load_cls = load.CommunityCreateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        rules = [
            ("communities_community", OperationType.INSERT),
            ("oaiserver_set", OperationType.INSERT),
        ]
        logo_rules = [
            *rules,
            ("files_bucket", OperationType.UPDATE),
            ("files_object", OperationType.INSERT),
            ("files_files", OperationType.INSERT),
            ("files_object", OperationType.UPDATE),
            ("files_files", OperationType.UPDATE),
            ("communities_community", OperationType.UPDATE),
            ("files_bucket", OperationType.UPDATE),
        ]

        ops = [(op["source"]["table"], op["op"]) for op in tx.operations]
        return ops in (rules, logo_rules)

    def _transform_data(self):
        """Transforms the data and returns dictionary."""
        payloads = []
        for op in self.tx.operations:
            self._microseconds_to_isodate(
                data=op["after"], fields=["created", "updated"]
            )
            # Only keep the "after" payload
            payloads.append(op["after"])

        community_src, oai_set_src, *files_payloads = payloads
        result = {
            "tx_id": self.tx.id,
            "community": ZenodoCommunityEntry().transform(community_src),
            "owner": ZenodoCommunityMemberEntry().transform(community_src),
            "oai_set": oai_set_src,
            "bucket": ZenodoCommunityFilesBucketEntry().transform(community_src),
        }

        # Yransform the logo data if there is one
        if files_payloads:
            # We only care about files-related ops
            _, ov1, f1, ov2, f2, _, _ = files_payloads

            # We "merge" the INSERT + UPDATE payloads
            file_instance = {**f1, **f2}
            object_version = {**ov1, **ov2}

            # We can safely assume that the bucket's size will only have the logo file
            result["bucket"]["size"] = file_instance["size"]
            # All logos keep the "logo" key
            object_version["key"] = "logo"
            community_file = ZenodoCommunityFileEntry().transform(community_src)

            result.update(
                {
                    "file_instance": file_instance,
                    "object_version": object_version,
                    "community_file": community_file,
                }
            )
        return result


class CommunityUpdateAction(TransformAction):
    """Zenodo to RDM community update action."""

    name = "community-update"
    load_cls = load.CommunityUpdateAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        rules = [
            ("communities_community", OperationType.UPDATE),
        ]
        new_logo_rules = [
            *rules,
            ("files_bucket", OperationType.UPDATE),
            ("files_object", OperationType.INSERT),
            ("files_files", OperationType.INSERT),
            ("files_object", OperationType.UPDATE),
            ("communities_community", OperationType.UPDATE),
            ("files_files", OperationType.UPDATE),
            ("files_bucket", OperationType.UPDATE),
        ]
        update_logo_rules = [
            *rules,
            ("files_bucket", OperationType.UPDATE),
            ("files_object", OperationType.UPDATE),  # "deletion" of old object version
            ("files_object", OperationType.INSERT),
            ("files_files", OperationType.INSERT),
            ("files_object", OperationType.UPDATE),
            ("communities_community", OperationType.UPDATE),
            ("files_files", OperationType.UPDATE),
            ("files_bucket", OperationType.UPDATE),
        ]

        ops = [(op["source"]["table"], op["op"]) for op in tx.operations]
        return ops in (rules, new_logo_rules, update_logo_rules)

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        payloads = []
        for op in self.tx.operations:
            self._microseconds_to_isodate(
                data=op["after"], fields=["created", "updated"]
            )
            # Only keep the "after" payload
            payloads.append(op["after"])

        community_src, *files_payloads = payloads
        result = {
            "tx_id": self.tx.id,
            "community": ZenodoCommunityEntry(partial=True).transform(community_src),
        }

        # Transform the logo data if there is one
        if files_payloads:
            # We only care about files-related ops.
            ov1, f1, ov2, _, f2, _ = files_payloads[-6:]

            # We "merge" the INSERT + UPDATE payloads
            file_instance = {**f1, **f2}
            object_version = {**ov1, **ov2}

            # All logos keep the "logo" key
            object_version["key"] = "logo"
            community_file = ZenodoCommunityFileEntry().transform(community_src)

            result.update(
                {
                    "file_instance": file_instance,
                    "object_version": object_version,
                    "community_file": community_file,
                }
            )
        return result


class CommunityDeleteAction(TransformAction):
    """Zenodo to RDM community delete action."""

    name = "community-delete"
    load_cls = load.CommunityDeleteAction

    @classmethod
    def matches_action(cls, tx):
        """Checks if the data corresponds with that required by the action."""
        rules = [
            ("communities_community", OperationType.DELETE),
        ]

        ops = [(op["source"]["table"], op["op"]) for op in tx.operations]
        return ops == rules

    def _transform_data(self):
        """Transforms the data and returns an instance of the mapped_cls."""
        return {
            "tx_id": self.tx.id,
            "community": {"slug": self.tx.operations[0]["after"]["id"]},
        }


COMMUNITY_ACTIONS = [
    CommunityCreateAction,
    CommunityDeleteAction,
    CommunityUpdateAction,
]
