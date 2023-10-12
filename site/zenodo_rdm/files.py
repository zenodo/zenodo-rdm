# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo files utilities."""

import mimetypes
from urllib.parse import urlsplit, urlunsplit

import requests
from flask import current_app, make_response, request
from invenio_files_rest.helpers import sanitize_mimetype
from invenio_files_rest.storage.pyfs import pyfs_storage_factory

try:
    from invenio_xrootd.storage import EOSFileStorage as BaseFileStorage
    from requests_kerberos import DISABLED, HTTPKerberosAuth
except ImportError:
    # fake requests_kerberos
    HTTPKerberosAuth = type("obj", (object,), {})
    DISABLED = 3
    # use base PyFSFileStorage instead
    from invenio_files_rest.storage.pyfs import PyFSFileStorage as BaseFileStorage


class EOSFilesOffload(BaseFileStorage):
    """Offload file downloads to another server."""

    def _get_eos_redirect_path(self):
        """Get the real path of the file streamed from another server."""
        host = current_app.config["ZENODO_EOS_OFFLOAD_HTTPHOST"]
        redirect_base_path = current_app.config["ZENODO_EOS_OFFLOAD_REDIRECT_BASE_PATH"]
        base_path = urlsplit(self.fileurl).path
        eos_resp = requests.get(
            f"{host}/{base_path}",
            auth=HTTPKerberosAuth(DISABLED),
            verify=False,
            allow_redirects=False,
        )
        if eos_resp.status_code != 307:
            raise Exception("EOS redirect failed")

        eos_url = eos_resp.next.url
        eos_url_parts = urlsplit(eos_url)
        redirect_path = f"{redirect_base_path}/{eos_url_parts.scheme}/{eos_url_parts.hostname}/{eos_url_parts.port}/{eos_url_parts.path}"
        return urlunsplit(("", "", redirect_path, eos_url_parts.query, ""))

    def send_file(self, filename, **kwargs):
        """Send file."""
        # No need to proxy HEAD requests to EOS
        should_offload = (
            request.method != "HEAD"
            and current_app.config["ZENODO_EOS_OFFLOAD_ENABLED"]
            and current_app.config["FILES_REST_XSENDFILE_ENABLED"]
        )

        if should_offload:
            response = make_response()

            try:
                response.headers["X-Accel-Redirect"] = self._get_eos_redirect_path()
            except Exception as ex:
                current_app.logger.error(ex)
                # fallback to normal file download
                return super().send_file(filename, **kwargs)

            response.headers["X-Accel-Buffering"] = "yes"
            response.headers["X-Accel-Limit-Rate"] = "off"

            mimetype = mimetypes.guess_type(filename)[0]
            if mimetype is not None:
                mimetype = sanitize_mimetype(mimetype, filename=filename)

            if mimetype is None:
                mimetype = "application/octet-stream"

            response.mimetype = mimetype

            # make the browser use the file download dialogue for the file
            response.headers[
                "Content-Disposition"
            ] = f'attachment; filename="{filename}"'

            # Security-related headers for the download (from invenio-files-rest)
            response.headers["Content-Security-Policy"] = "default-src 'none';"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Download-Options"] = "noopen"
            response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
            response.headers["X-Frame-Options"] = "deny"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            return response
        else:
            return super().send_file(filename, **kwargs)


def storage_factory(**kwargs):
    """Create custom storage factory to enable file offloading."""
    return pyfs_storage_factory(filestorage_class=EOSFilesOffload, **kwargs)
