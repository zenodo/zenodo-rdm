# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator parent record transformer entries."""


from invenio_rdm_migrator.transform import Entry

from ...errors import NoConceptRecidForDraft


class ParentRecordEntry(Entry):
    """Parent record transform entry class."""

    def __init__(self, partial=False):
        """Constructor.

        :param partial: a boolean enabling partial transformations, i.e. missing keys.
        """
        self.partial = partial

    def _communities(self, entry):
        communities = entry["json"].get("communities")
        if communities:
            slugs = [slug for slug in communities]
            return {"ids": slugs, "default": slugs[0]}
        return {}

    def transform(self, entry):
        """Transform a parent."""
        transformed = {}

        # both created and updated are the same as the record
        keys = ["created", "updated", "version_id"]
        for key in keys:
            try:
                transformed[key] = entry[key]
            except KeyError as ex:
                if not self.partial:
                    raise KeyError(ex)
                pass
        if "json" in entry:
            # check if conceptrecid exists and bail otherwise. should not happen!
            # this is the case for some deposits and they should be fixed in prod as it
            parent_pid = entry["json"].get("conceptrecid")
            if not parent_pid:
                # we raise so the error logger writes these cases in the log file
                raise NoConceptRecidForDraft(draft=entry)

            transformed["json"] = {
                # loader is responsible for creating/updating if the PID exists.
                "id": parent_pid,
                "access": {
                    "owned_by": [{"user": o} for o in entry["json"].get("owners", [])]
                },
                "communities": self._communities(entry),
            }
        elif not self.partial:
            raise KeyError("json")
        # else, pass

        return transformed
