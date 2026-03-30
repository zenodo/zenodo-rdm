# SPDX-FileCopyrightText: 2022-2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo migrator users transformers."""

from invenio_rdm_migrator.streams.users import UserTransform

from .entries.users import ZenodoUserEntry


class ZenodoUserTransform(UserTransform):
    """Zenodo user transform."""

    def _user(self, entry):
        """Transform the user."""
        return ZenodoUserEntry().transform(entry)

    def _session_activity(self, entry):
        """Transform the session activity."""
        return entry.get("session_activity")

    def _tokens(self, entry):
        """Transform the tokens."""
        return entry.get("tokens")

    def _applications(self, entry):
        """Transform the applications."""
        # TODO
        pass

    def _oauth(self, entry):
        """Transform the OAuth accounts."""
        # TODO
        pass

    def _identities(self, entry):
        """Transform the identities."""
        data = entry.get("identities")
        return [
            {
                "id": i["id"],
                "created": i["created"],
                "updated": i["updated"],
                "method": i["method"],
            }
            for i in data or []
        ]
