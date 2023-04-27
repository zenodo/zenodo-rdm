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

from .generators import IfFilesRestrictedForCommunity


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
