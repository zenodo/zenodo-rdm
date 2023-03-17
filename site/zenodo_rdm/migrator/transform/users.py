# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo migrator users transformers."""

from datetime import datetime

from invenio_rdm_migrator.streams.users import UserEntry, UserTransform


class ZenodoUserEntry(UserEntry):
    """Transform a single user entry."""

    def _id(self, entry):
        """Returns the user ID."""
        return entry["id"]

    def _created(self, entry):
        """Returns the creation date."""
        return entry.get("created", datetime.utcnow().isoformat())

    def _updated(self, entry):
        """Returns the update date."""
        return entry.get("updated", datetime.utcnow().isoformat())

    def _version_id(self, entry):
        """Returns the version id."""
        return entry.get("version_id", 1)

    def _email(self, entry):
        """Returns the email."""
        return entry["email"]

    def _active(self, entry):
        """Returns if the user is active."""
        return entry["active"]

    def _password(self, entry):
        """Returns the password."""
        return entry.get("password")

    def _confirmed_at(self, entry):
        """Returns the confirmation date."""
        return entry.get("confirmed_at")

    def _username(self, entry):
        """Returns the username."""
        return entry.get("username")

    def _displayname(self, entry):
        """Returns the displayname."""
        return entry.get("displayname")

    def _profile(self, entry):
        """Returns the profile."""
        return {
            "full_name": entry.get("full_name"),
        }

    def _preferences(self, entry):
        """Returns the preferences."""
        return {
            "visibility": "restricted",
            "email_visibility": "restricted",
        }

    def _login_information(self, entry):
        """Returns the login information."""
        return {
            "last_login_at": entry.get("last_login_at"),
            "current_login_at": entry.get("current_login_at"),
            "last_login_ip": entry.get("last_login_ip"),
            "current_login_ip": entry.get("current_login_ip"),
            "login_count": entry.get("login_count"),
        }


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
