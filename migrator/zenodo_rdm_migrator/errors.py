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
        return f"No conceptrecid for draft: {self.draft}"


class InvalidTombstoneRecord(Exception):
    """Invalid tombstone record error."""

    @property
    def description(self):
        """Exception's description."""
        return "Not possible to generate tombstone record from entry."


class InvalidIdentifier(Exception):
    """Invalid identifiers, for example a missing scheme."""

    def __init__(self, identifier):
        """Initialise error."""
        self.identifier = identifier

    @property
    def description(self):
        """Exception's description."""
        return f"Invalid identifier {self.identifier}"
