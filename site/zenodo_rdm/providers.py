# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# Zenodo is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo PID providers."""

import copy

from invenio_rdm_records import config as rdm_records_config
from invenio_rdm_records.services.pids.providers.base import PIDProvider


class NoParentDOIPID:
    """Stub no parent DOI PID."""

    @property
    def id(self):
        """Return id."""
        return None

    @property
    def pid_type(self):
        """Return pid_type."""
        return None

    @property
    def pid_type(self):
        """Return pid_type."""
        return None

    @property
    def pid_value(self):
        """Return pid_value."""
        return None

    @property
    def pid_provider(self):
        """Return pid_provider."""
        return None

    @property
    def status(self):
        """Return status."""
        return None

    @property
    def object_type(self):
        """Return object_type."""
        return None

    @property
    def object_uuid(self):
        """Return object_uuid."""
        return None

    @classmethod
    def create(cls, *args, **kwargs):
        """Create a new persistent identifier with specific type and value."""
        return cls()

    @classmethod
    def get(cls, *args, **kwargs):
        """Get persistent identifier."""
        return cls()

    @classmethod
    def get_by_object(cls, *args, **kwargs):
        """Get a persistent identifier for a given object."""
        return cls()

    def has_object(self):
        """Determine if this PID has an assigned object."""
        return True

    def get_assigned_object(self, *args, **kwargs):
        """Return the current assigned object UUID."""
        return None

    def assign(self, *args, **kwargs):
        """Assign this persistent identifier to a given object."""
        return True

    def unassign(self):
        """Unassign the registered object."""
        return True

    def get_redirect(self):
        """Get redirected persistent identifier."""
        return None

    def redirect(self, *args, **kwargs):
        """Redirect persistent identifier to another persistent identifier."""
        return True

    def reserve(self):
        """Reserve the persistent identifier."""
        return True

    def register(self):
        """Register the persistent identifier with the provider."""
        return True

    def delete(self):
        """Delete the persistent identifier."""
        return True

    def sync_status(self, status):
        """Synchronize persistent identifier status."""
        return True

    def is_redirected(self):
        """Return true if the persistent identifier has been registered."""
        return False

    def is_registered(self):
        """Return true if the persistent identifier has been registered."""
        return True

    def is_deleted(self):
        """Return true if the persistent identifier has been deleted."""
        return False

    def is_new(self):
        """Return true if the PID is new."""
        return False

    def is_reserved(self):
        """Return true if the PID has been reserved."""
        return False

    def __repr__(self):
        """Get representation of object."""
        return "<NoParentDOI>"


class LegacyParentDOIProvider(PIDProvider):
    """Legacy parent DOI provider."""

    def can_modify(self, pid, **kwargs):
        """Checks if the given PID can be modified."""
        return False

    def get(self, pid_value, pid_provider=None):
        """Get a persistent identifier for this provider."""
        return NoParentDOIPID()

    def create(self, record, pid_value=None, status=None, **kwargs):
        """Get or create the PID with given value for the given record."""
        return NoParentDOIPID()

    def reserve(self, pid, **kwargs):
        """Reserve a persistent identifier."""
        return True

    def register(self, pid, **kwargs):
        """Register a persistent identifier."""
        return True

    def update(self, pid, **kwargs):
        """Update information about the persistent identifier."""
        pass

    def delete(self, pid, **kwargs):
        """Delete a persistent identifier."""
        return None

    def validate(self, record, identifier=None, provider=None, **kwargs):
        """Validate the attributes of the identifier."""
        return True, []


RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS = [
    *rdm_records_config.RDM_PARENT_PERSISTENT_IDENTIFIER_PROVIDERS,
    # Legacy provider for old records without a concept DOI
    LegacyParentDOIProvider("legacy", pid_type="doi"),
]


RDM_PARENT_PERSISTENT_IDENTIFIERS = copy.deepcopy(
    rdm_records_config.RDM_PARENT_PERSISTENT_IDENTIFIERS
)
RDM_PARENT_PERSISTENT_IDENTIFIERS["doi"]["providers"] = [
    "datacite",  # Order matters! First name is the "default" provider
    "legacy",
]
