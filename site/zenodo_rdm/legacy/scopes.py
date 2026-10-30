# SPDX-FileCopyrightText: 2023-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""OAuth2 legacy token scopes."""

from flask import abort, request
from flask_login import current_user
from invenio_i18n import lazy_gettext as _
from invenio_oauth2server.decorators import require_oauth_scopes
from invenio_oauth2server.models import Scope

deposit_write_scope = Scope(
    id_="deposit:write",
    group="deposit",
    help_text=_("Allow upload (but not publishing)."),
)
"""Allow upload (but not publishing)."""

deposit_actions_scope = Scope(
    id_="deposit:actions",
    group="deposit",
    help_text=_("Allow publishing of uploads."),
)
"""Allow publishing of uploads."""

_write = (deposit_write_scope.id,)
_actions = (deposit_actions_scope.id,)

LEGACY_ENDPOINT_SCOPES = {
    # Depositions
    "legacy_records.create": _write,
    "legacy_records.update_draft": _write,
    "legacy_records.delete_draft": _write,
    "legacy_records.publish": _actions,
    "legacy_records.edit": _actions,
    "legacy_records.discard_draft": _actions,
    "legacy_records.new_version": _actions,
    # Deposition files
    "legacy_draft_files.create": _write,
    "legacy_draft_files.delete": _write,
    # Files-REST
    "legacy_files_rest.set_object": _write,
    "legacy_files_rest.delete_object": _write,
    # Extra formats
    "legacy_draft_extra_formats.put": _write,
    "legacy_draft_extra_formats.delete": _write,
}
"""OAuth scopes required by each legacy endpoint.

Endpoints not listed here, such as reads, keep relying only on record permissions.
"""


def require_legacy_scopes():
    """Require authentication and the endpoint's OAuth scopes.

    Meant to be registered as a ``before_request`` hook on the legacy blueprints.
    Bearer tokens are already verified by Invenio-OAuth2Server before the request
    reaches this hook. Users authenticated with a session are not restricted by
    scopes. CORS preflight requests carry no credentials, so they are let through.
    """
    if request.method == "OPTIONS":
        return
    scopes = LEGACY_ENDPOINT_SCOPES.get(request.endpoint)
    if scopes is None:
        return
    if not current_user.is_authenticated:
        abort(401)
    require_oauth_scopes(*scopes)(lambda: None)()
