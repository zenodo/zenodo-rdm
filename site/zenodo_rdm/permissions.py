# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo permissions."""

from invenio_administration.generators import Administration
from invenio_communities.permissions import CommunityPermissionPolicy
from invenio_rdm_records.services.generators import (
    AccessGrant,
    CommunityInclusionReviewers,
    IfDeleted,
    IfExternalDOIRecord,
    IfNewRecord,
    IfRecordDeleted,
    IfRestricted,
    RecordCommunitiesAction,
    RecordOwners,
    ResourceAccessToken,
    SecretLinks,
    SubmissionReviewer,
)
from invenio_rdm_records.services.permissions import RDMRecordPermissionPolicy
from invenio_records_permissions.generators import (
    Disable,
    Generator,
    IfConfig,
    SystemProcess,
)
from invenio_records_resources.services.files.generators import IfTransferType
from invenio_records_resources.services.files.transfer import (
    LOCAL_TRANSFER_TYPE,
)
from invenio_users_resources.services.permissions import UserManager

from .generators import (
    ExternalDOIFilesManager,
    IfFilesRestrictedForCommunity,
    IfRecordManagementAllowedForCommunity,
    MediaFilesManager,
)
from .legacy.tokens import LegacySecretLinkNeed


class LegacySecretLinks(Generator):
    """Legacy secret Links for records."""

    def needs(self, record=None, **kwargs):
        """Set of Needs granting permission."""
        if not record:
            return []
        return [LegacySecretLinkNeed(record["id"])]


class ZenodoRDMRecordPermissionPolicy(RDMRecordPermissionPolicy):
    """Access control configuration for records."""

    #
    # High-level permissions (used by low-level)
    #
    can_manage = [
        IfRecordManagementAllowedForCommunity(
            then_=RDMRecordPermissionPolicy.can_manage,
            else_=[
                RecordOwners(),
                AccessGrant("manage"),
                SystemProcess(),
            ],  # hide from community curators
        )
    ]
    can_curate = can_manage + [AccessGrant("edit"), SecretLinks("edit")]
    can_review = can_curate + [SubmissionReviewer()]
    can_preview = can_curate + [
        AccessGrant("preview"),
        SecretLinks("preview"),
        LegacySecretLinks(),
        SubmissionReviewer(),
        UserManager,
    ]
    can_view = can_preview + [
        AccessGrant("view"),
        SecretLinks("view"),
        SubmissionReviewer(),
        CommunityInclusionReviewers(),
        RecordCommunitiesAction("view"),
    ]

    #
    #  Records
    #
    # Allow reading metadata of a record
    can_read = [
        IfRestricted("record", then_=can_view, else_=RDMRecordPermissionPolicy.can_all),
    ]

    # Used for search filtering of deleted records
    # cannot be implemented inside can_read - otherwise permission will
    # kick in before tombstone renders
    can_read_deleted = [
        IfRecordDeleted(
            then_=[UserManager, SystemProcess()],
            else_=can_read,
        )
    ]
    can_read_deleted_files = can_read_deleted
    can_media_read_deleted_files = can_read_deleted_files

    #
    # Drafts
    #
    # Allow reading metadata of a draft
    can_read_draft = can_preview
    # Allow reading files of a draft
    can_draft_read_files = can_preview + [ResourceAccessToken("read")]
    # Allow updating metadata of a draft
    can_update_draft = can_review
    # Allow uploading, updating and deleting files in drafts
    can_draft_create_files = can_review
    can_draft_set_content_files = [
        # review is the same as create_files
        IfTransferType(LOCAL_TRANSFER_TYPE, can_review),
        SystemProcess(),
    ]
    can_draft_get_content_files = [
        # preview is same as read_files
        IfTransferType(LOCAL_TRANSFER_TYPE, can_draft_read_files),
        SystemProcess(),
    ]
    can_draft_commit_files = [
        # review is the same as create_files
        IfTransferType(LOCAL_TRANSFER_TYPE, can_review),
        SystemProcess(),
    ]
    can_draft_update_files = can_review
    can_draft_delete_files = can_review
    # Allow enabling/disabling files
    can_manage_files = [
        IfConfig(
            "RDM_ALLOW_METADATA_ONLY_RECORDS",
            then_=[
                IfNewRecord(
                    then_=RDMRecordPermissionPolicy.can_authenticated, else_=can_review
                )
            ],
            else_=[],
        ),
    ]
    # Allow managing record access
    can_manage_record_access = [
        IfConfig(
            "RDM_ALLOW_RESTRICTED_RECORDS",
            then_=[
                IfNewRecord(
                    then_=RDMRecordPermissionPolicy.can_authenticated, else_=can_review
                )
            ],
            else_=[],
        )
    ]

    #
    # PIDs
    #
    can_pid_create = can_review
    can_pid_register = can_review
    can_pid_update = can_review
    can_pid_discard = can_review
    can_pid_delete = can_review

    #
    # Actions
    #
    # Allow to put a record in edit mode (create a draft from record)
    can_edit = [IfDeleted(then_=[Disable()], else_=can_curate)]
    # Allow deleting/discarding a draft and all associated files
    can_delete_draft = can_curate
    # Allow creating a new version of an existing published record.
    can_new_version = [
        IfConfig(
            "RDM_ALLOW_EXTERNAL_DOI_VERSIONING",
            then_=can_curate,
            else_=[IfExternalDOIRecord(then_=[Disable()], else_=can_curate)],
        ),
    ]
    # Allow publishing a new record or changes to an existing record.
    can_publish = can_review
    # Allow lifting a record or draft.
    can_lift_embargo = can_manage

    #
    # Record communities
    #
    # Who can add record to a community
    can_add_community = can_manage

    # Allow reading the files of a record
    # Hide record's files from community
    can_read_files_owner = [RecordOwners(), SecretLinks("view"), SystemProcess()]
    # Show record's files to community
    can_read_files_community = [
        IfRestricted(
            "files",
            then_=can_view,
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
        IfTransferType(LOCAL_TRANSFER_TYPE, can_read_files),
        SystemProcess(),
    ]

    # Media files
    can_draft_media_create_files = [MediaFilesManager(), SystemProcess()]
    can_draft_media_read_files = can_draft_media_create_files
    can_draft_media_set_content_files = [
        IfTransferType(LOCAL_TRANSFER_TYPE, can_draft_media_create_files),
        SystemProcess(),
    ]
    can_draft_media_get_content_files = [
        # preview is same as read_files
        IfTransferType(LOCAL_TRANSFER_TYPE, can_get_content_files),
        SystemProcess(),
    ]
    can_draft_media_commit_files = [
        # review is the same as create_files
        IfTransferType(LOCAL_TRANSFER_TYPE, can_draft_media_create_files),
        SystemProcess(),
    ]
    can_draft_media_update_files = can_draft_media_create_files
    # from the core
    can_draft_media_delete_files = can_draft_media_create_files

    #
    # Media files - record
    #
    can_media_read_files = [
        IfRestricted("record", then_=can_view, else_=RDMRecordPermissionPolicy.can_all),
        ResourceAccessToken("read"),
    ]
    can_media_get_content_files = [
        # note: even though this is closer to business logic than permissions,
        # it was simpler and less coupling to implement this as permission check
        IfTransferType(LOCAL_TRANSFER_TYPE, can_read_files),
        SystemProcess(),
    ]

    can_moderate = [
        # moderators
        UserManager,
        SystemProcess(),
    ]
    can_media_create_files = [SystemProcess()]
    can_media_set_content_files = [SystemProcess()]
    can_media_commit_files = [SystemProcess()]
    can_media_update_files = [SystemProcess()]
    can_media_delete_files = [SystemProcess()]

    can_modify_locked_files = [
        Administration(),
        UserManager,
        SystemProcess(),
        IfExternalDOIRecord(then_=[ExternalDOIFilesManager()], else_=[]),
    ]


class ZenodoCommunityPermissionPolicy(CommunityPermissionPolicy):
    """Permissions for Community CRUD operations."""

    can_moderate = [
        # moderators
        UserManager,
        SystemProcess(),
    ]

    can_rename = [SystemProcess()]
