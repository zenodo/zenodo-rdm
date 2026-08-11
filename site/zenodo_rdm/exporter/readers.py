# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read records for export."""

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from invenio_access.permissions import any_user
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service


def read_records(community_slug):
    """Return a lazy stream of records to export."""
    community_id = None
    if community_slug:
        community_id = (
            db.session.query(CommunityMetadata.id)
            .filter(CommunityMetadata.slug == community_slug)
            .one()[0]
        )

    identity = AnonymousIdentity()
    with current_app.test_request_context():
        identity_changed.send(current_app, identity=identity)
        identity.provides.add(any_user)

    # RecordService.scan() does not let callers change the scroll lifetime.
    records = current_rdm_records_service
    params = {"allversions": True, "include_deleted": True}
    records.require_permission(identity, "search")
    result = (
        records._search(
            "scan",
            identity,
            params,
            None,
            q=f"parent.communities.ids:{community_id}" if community_id else "",
        )
        .params(scroll="15m")
        .scan()
    )
    return records.result_list(
        records,
        identity,
        result,
        params,
        links_tpl=None,
        links_item_tpl=records.links_item_tpl,
        expandable_fields=records.expandable_fields,
        expand=False,
    ).hits
