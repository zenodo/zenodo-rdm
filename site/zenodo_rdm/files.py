# SPDX-FileCopyrightText: 2023 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Zenodo files utilities."""

import mimetypes
import unicodedata
from urllib.parse import quote, urlsplit, urlunsplit

import requests
from flask import current_app, make_response, request
from invenio_files_rest.helpers import sanitize_mimetype
from invenio_files_rest.storage.pyfs import PyFSFileStorage, pyfs_storage_factory

try:
    from invenio_xrootd.storage import EOSFileStorage
    from requests_kerberos import DISABLED, HTTPKerberosAuth
except ImportError:
    # fake requests_kerberos
    HTTPKerberosAuth = type("obj", (object,), {})
    DISABLED = 3
    # use base PyFSFileStorage instead
    EOSFileStorage = PyFSFileStorage


class FilesOffload:
    """Offload file downloads to nginx via X-Accel-Redirect."""

    offload_enabled_config = None

    def _get_redirect_path(self):
        """Get the nginx internal redirect path of the file."""
        raise NotImplementedError()

    def send_file(
        self,
        filename,
        mimetype=None,
        restricted=True,
        checksum=None,
        trusted=False,
        chunk_size=None,
        as_attachment=False,
        **kwargs,
    ):
        """Send file."""
        # No need to offload HEAD requests
        should_offload = (
            request.method != "HEAD"
            and current_app.config[self.offload_enabled_config]
            and current_app.config["FILES_REST_XSENDFILE_ENABLED"]
        )

        if should_offload:
            response = make_response()

            try:
                response.headers["X-Accel-Redirect"] = self._get_redirect_path()
            except Exception as ex:
                current_app.logger.exception(ex)
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

            # Force Content-Disposition for application/octet-stream to prevent
            # Content-Type sniffing.
            # (from invenio-files-rest)
            if as_attachment or mimetype == "application/octet-stream":
                # see https://github.com/pallets/werkzeug/blob/main/src/werkzeug/utils.py#L456-L465
                try:
                    filename.encode("ascii")
                except UnicodeEncodeError:
                    simple = unicodedata.normalize("NFKD", filename)
                    simple = simple.encode("ascii", "ignore").decode("ascii")
                    # safe = RFC 5987 attr-char
                    quoted = quote(filename, safe="!#$&+-.^_`|~")
                    filenames = {"filename": simple, "filename*": f"UTF-8''{quoted}"}
                else:
                    filenames = {"filename": filename}
                response.headers.set("Content-Disposition", "attachment", **filenames)
            else:
                response.headers.set("Content-Disposition", "inline")

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


class EOSFilesOffload(FilesOffload, EOSFileStorage):
    """Offload EOS file downloads to the EOS server."""

    offload_enabled_config = "ZENODO_EOS_OFFLOAD_ENABLED"

    def _get_auth_session(self):
        """Get a requests session with authentication configured.

        If X.509 is enabled, it will be used, otherwise kerberos will be used.
        """
        s = requests.Session()
        x509_enabled = current_app.config.get("ZENODO_EOS_OFFLOAD_AUTH_X509", False)
        cert = current_app.config.get("ZENODO_EOS_OFFLOAD_X509_CERT_PATH")
        key = current_app.config.get("ZENODO_EOS_OFFLOAD_X509_KEY_PATH")
        if x509_enabled and cert and key:
            s.cert = (cert, key)
            s.verify = False
        else:
            # Default to kerberos
            s.auth = HTTPKerberosAuth(DISABLED)
            s.verify = False
        return s

    def _get_redirect_path(self):
        """Get the real path of the file streamed from another server."""
        host = current_app.config["ZENODO_EOS_OFFLOAD_HTTPHOST"]
        redirect_base_path = current_app.config["ZENODO_EOS_OFFLOAD_REDIRECT_BASE_PATH"]
        base_path = urlsplit(self.fileurl).path
        session = self._get_auth_session()
        eos_resp = session.get(
            f"{host}/{base_path}",
            allow_redirects=False,
            timeout=5,
        )
        if eos_resp.status_code != 307:
            raise Exception(
                f"EOS redirect failed "
                f"with response code:{eos_resp.status_code} "
                f" and error: {eos_resp.text}"
            )

        eos_url = eos_resp.next.url
        eos_url_parts = urlsplit(eos_url)
        redirect_path = f"{redirect_base_path}/{eos_url_parts.scheme}/{eos_url_parts.hostname}/{eos_url_parts.port}/{eos_url_parts.path}"
        return urlunsplit(("", "", redirect_path, eos_url_parts.query, ""))


class LocalFilesOffload(FilesOffload, PyFSFileStorage):
    """Offload local volume file downloads (e.g. IIIF .ptif media files)."""

    offload_enabled_config = "ZENODO_LOCAL_OFFLOAD_ENABLED"

    def _get_redirect_path(self):
        """Get the nginx internal path of a file stored on a local volume."""
        redirect_base_path = current_app.config[
            "ZENODO_LOCAL_OFFLOAD_REDIRECT_BASE_PATH"
        ]
        return f"{redirect_base_path}{quote(self.fileurl)}"


def _offload_storage(fileurl, **kwargs):
    """Create the offload storage matching the file URL."""
    if urlsplit(fileurl).scheme in ("root", "roots"):
        return EOSFilesOffload(fileurl, **kwargs)
    return LocalFilesOffload(fileurl, **kwargs)


def storage_factory(**kwargs):
    """Create custom storage factory to enable file offloading."""
    # pyfs_storage_factory only calls ``filestorage_class`` with the resolved URL,
    # so a function can pick the class per URL scheme
    return pyfs_storage_factory(filestorage_class=_offload_storage, **kwargs)
