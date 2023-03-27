# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator requests transformers."""

from datetime import datetime, timedelta

from invenio_rdm_migrator.streams.requests import (
    InclusionRequestEntry,
    RequestTransform,
)


class ZenodoRequestEntry(InclusionRequestEntry):
    """Transform a single request entry."""

    def _created(self, entry):
        """Returns the creation date of the request."""
        return entry["created"]

    def _updated(self, entry):
        """Returns the creation date of the request."""
        return entry["updated"]

    def _version_id(self, entry):
        """Returns the version id of the request."""
        return 1

    def _number(self, entry):
        """Returns the request number."""
        # FIXME: is this a sequence number?
        pass

    def _expires_at(self, entry):
        """Returns the request expiration date.

        We want to expire requests in a year from now.
        """
        next_year = datetime.today() + timedelta(days=365)
        return next_year.isoformat()

    # JSON related functions
    def _title(self, entry):
        """Returns the request title."""
        return entry["title"]

    def _topic(self, entry):
        """Returns the request topic."""
        return {"record": entry["recid"]}

    def _receiver(self, entry):
        """Returns the request receiver."""
        return {"community": entry["id_community"]}

    def _created_by(self, entry):
        """Returns the request creation reference."""
        return {"user": entry["owners"]}


class ZenodoRequestTransform(RequestTransform):
    """Transform a Zenodo request into RDM."""

    def _request(self, entry):
        """Transform the request."""
        return ZenodoRequestEntry().transform(entry)
