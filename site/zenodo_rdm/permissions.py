# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy permissions."""

from invenio_rdm_records.services.generators import (
    IfFileIsLocal,
    IfRestricted,
    RecordOwners,
    SecretLinks,
)
from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.generators import SystemProcess

from .generators import IfFilesRestrictedForCommunity, MediaFilesManager


class ZenodoRDMRecordPermissionPolicy(RDMRecordPermissionPolicy):
    """Access control configuration for records."""

    # Allow reading the files of a record
    # Hide record's files from community
    can_read_files_owner = [RecordOwners(), SecretLinks("view"), SystemProcess()]
    # Show record's files to community
    can_read_files_community = [
        IfRestricted(
            "files",
            then_=RDMRecordPermissionPolicy.can_view,
            else_=RDMRecordPermissionPolicy.can_all,
        ),
    ]
    can_read_files = [
        IfFilesRestrictedForCommunity(
            then_=can_read_files_owner, else_=can_read_files_community
        ),
    ]
    can_get_content_files = [
        # note: even though this is closer to business logic than permissions,
        # it was simpler and less coupling to implement this as permission check
        IfFileIsLocal(then_=can_read_files, else_=[SystemProcess()])
    ]

    # media files
    can_draft_media_create_files = [MediaFilesManager(), SystemProcess()]
    can_draft_media_read_files = [can_read_files_owner]
    can_draft_media_set_content_files = [
        IfFileIsLocal(then_=can_draft_media_create_files, else_=[SystemProcess()])
    ]
    can_draft_media_get_content_files = [
        # preview is same as read_files
        IfFileIsLocal(then_=can_draft_media_create_files, else_=[SystemProcess()])
    ]
    can_draft_media_commit_files = [
        # review is the same as create_files
        IfFileIsLocal(then_=can_draft_media_create_files, else_=[SystemProcess()])
    ]
    can_draft_media_update_files = can_draft_media_create_files
    # from the core
    can_draft_media_delete_files = can_draft_media_create_files
