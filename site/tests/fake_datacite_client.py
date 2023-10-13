# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
# Copyright (C) 2022 Northwestern University.
#
# Zenodo-RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Fake Datacite client."""

from unittest.mock import Mock

from idutils import normalize_doi
from invenio_rdm_records.services.pids import providers


class FakeDataCiteRESTClient:
    """DataCite REST API client wrapper."""

    def __init__(
        self, username, password, prefix, test_mode=False, url=None, timeout=None
    ):
        """Initialize the REST client wrapper.

        :param username: DataCite username.
        :param password: DataCite password.
        :param prefix: DOI prefix (or CFG_DATACITE_DOI_PREFIX).
        :param test_mode: use test URL when True
        :param url: DataCite API base URL.
        :param timeout: Connect and read timeout in seconds. Specify a tuple
            (connect, read) to specify each timeout individually.
        """
        self.username = str(username)
        self.password = str(password)
        self.prefix = str(prefix)

        if test_mode:
            self.api_url = "https://api.test.datacite.org/"
        else:
            self.api_url = url or "https://api.datacite.org/"

        if not self.api_url.endswith("/"):
            self.api_url += "/"

        self.timeout = timeout

    def public_doi(self, metadata, url, doi=None):
        """Create a public doi ... not.

        :param metadata: JSON format of the metadata.
        :param doi: DOI (e.g. 10.123/456)
        :param url: URL where the doi will resolve.
        :return:
        """
        return Mock()

    def update_doi(self, doi, metadata=None, url=None):
        """Update the metadata or url for a DOI ... not.

        :param url: URL where the doi will resolve.
        :param metadata: JSON format of the metadata.
        :return:
        """
        return Mock()

    def delete_doi(self, doi):
        """Delete a doi ... not.

        This will only work for draft dois

        :param doi: DOI (e.g. 10.123/456)
        :return:
        """
        return Mock()

    def hide_doi(self, doi):
        """Hide a previously registered DOI ... not.

        This DOI will no
        longer be found in DataCite Search

        :param doi: DOI to hide e.g. 10.12345/1.
        :return:
        """
        return Mock()

    def show_doi(self, doi):
        """Show a previously hidden DOI ... not.

        This DOI will no
        longer be found in DataCite Search

        :param doi: DOI to hide e.g. 10.12345/1.
        :return:
        """
        return Mock()

    def check_doi(self, doi):
        """Check doi structure.

        Check that the doi has a form
        12.12345/123 with the prefix defined
        """
        # If prefix is in doi
        if "/" in doi:
            split = doi.split("/")
            prefix = split[0]
            if prefix != self.prefix:
                # Provided a DOI with the wrong prefix
                raise ValueError(
                    "Wrong DOI {0} prefix provided, it should be "
                    "{1} as defined in the rest client".format(prefix, self.prefix)
                )
        else:
            doi = f"{self.prefix}/{doi}"
        return normalize_doi(doi)

    def __repr__(self):
        """Create string representation of object."""
        return f"<FakeDataCiteRESTClient: {self.username}>"


class FakeDataCiteClient(providers.DataCiteClient):
    """Fake DataCite Client."""

    @property
    def api(self):
        """Datacite REST API client instance."""
        if self._api is None:
            self.check_credentials()
            self._api = FakeDataCiteRESTClient(
                self.cfg("username"),
                self.cfg("password"),
                self.cfg("prefix"),
                self.cfg("test_mode", True),
            )
        return self._api
