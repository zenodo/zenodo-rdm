# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo legacy permissions generators."""

from invenio_rdm_records.services.generators import IfRestricted
from invenio_records.dictutils import dict_lookup


class IfFilesRestrictedForCommunity(IfRestricted):
    """Conditional generator for files restriction for community."""

    def __init__(self, then_, else_):
        """Constructor."""
        super().__init__("files", then_, else_)

    def _condition(self, record, **kwargs):
        """Check if community can access restricted files of the migrated record."""
        try:
            can_community_read_files = dict_lookup(
                record.parent, "permission_flags.can_community_read_files"
            )
        except KeyError:
            can_community_read_files = True

        is_restricted = super()._condition(record, **kwargs)
        if is_restricted:
            return not can_community_read_files
        else:
            return False
