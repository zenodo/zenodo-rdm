# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo files utilities."""

import mimetypes
from urllib.parse import urlsplit, urlunsplit

from flask import current_app, make_response, request
import requests
from requests_kerberos import HTTPKerberosAuth, DISABLED

from invenio_files_rest.helpers import sanitize_mimetype
from invenio_files_rest.storage.pyfs import pyfs_storage_factory
from invenio_xrootd.storage import EOSFileStorage

class EOSFilesOffload(EOSFileStorage):
    """."""

    def _get_eos_redirect_path(self):
        """."""
        host = current_app.config["ZENODO_EOS_OFFLOAD_HTTPHOST"]
        redirect_base_path = current_app.config["ZENODO_EOS_OFFLOAD_REDIRECT_BASE_PATH"]
        current_app.logger.info("** inside _get_eos_redirect_path")
        current_app.logger.info(f"host: {host}, redirect_base_path: {redirect_base_path}, self.fileurl: {self.fileurl}")
        base_path = urlsplit(self.fileurl).path
        current_app.logger.info(f"base_path: {base_path}, request: {'{host}/{path}'.format(host=host, path=base_path)}")
        eos_resp = requests.get(
            "{host}/{path}".format(host=host, path=base_path),
            auth=HTTPKerberosAuth(DISABLED),
            verify=False,
            allow_redirects=False,
        )
        current_app.logger.info(f"response: {eos_resp}")
        assert eos_resp.status_code == 307
        eos_url = eos_resp.next.url
        eos_url_parts = urlsplit(eos_url)
        current_app.logger.info(f"EOS response - next url: {eos_url}, eos_url_parts: {eos_url_parts}")
        redirect_path = f"{redirect_base_path}/{eos_url_parts.scheme}/{eos_url_parts.hostname}/{eos_url_parts.port}/{eos_url_parts.path}"
        current_app.logger.info(f"Redirect path: {redirect_path}")
        done = urlunsplit(("", "", redirect_path, eos_url_parts.query, ""))
        current_app.logger.info(f"done: {done}")
        return done

    def send_file(self, filename, **kwargs):
        import logging
        current_app.logger.setLevel(logging.INFO)
        current_app.logger.root.setLevel(logging.INFO)
        current_app.logger.handlers[0].setLevel(logging.INFO)
        # No need to proxy HEAD requests to EOS
        should_offload = request.method != "HEAD" and \
            current_app.config["ZENODO_EOS_OFFLOAD_ENABLED"] and \
            current_app.config["FILES_REST_XSENDFILE_ENABLED"]
        # test.json
        current_app.logger.info(f"Send file {filename}")
        # GET, True, True
        current_app.logger.info(f"request.method: {request.method}, ZENODO_EOS_OFFLOAD_ENABLED: {current_app.config['ZENODO_EOS_OFFLOAD_ENABLED']}, FILES_REST_XSENDFILE_ENABLED: {current_app.config['FILES_REST_XSENDFILE_ENABLED']} ")
        if should_offload:
            response = make_response()

            current_app.logger.info("Making response")
            response.headers["X-Accel-Redirect"] = self._get_eos_redirect_path()
            response.headers["X-Accel-Buffering"] = "yes"
            response.headers["X-Accel-Limit-Rate"] = "off"
            current_app.logger.info("Response redirect done")

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
            current_app.logger.info("Response headers:")
            current_app.logger.info(response.headers)
            return response
        else:
            current_app.logger.info("SHOULD NOT OFFLOAD")
            return super().send_file(filename, **kwargs)


def storage_factory(**kwargs):
    return pyfs_storage_factory(filestorage_class=EOSFilesOffload, **kwargs)
