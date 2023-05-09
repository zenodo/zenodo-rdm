# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator error classes."""


class NoConceptRecidForDraft(Exception):
    """No conceptrecid error."""

    def __init__(self, draft):
        """Initialise error."""
        self.draft = draft

    @property
    def description(self):
        """Exception's description."""
        return "No conceptrecid for draft: {draft}".format(draft=self.draft)
