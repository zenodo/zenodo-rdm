# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Utils for zenodo migrator module."""

from pathlib import Path

import yaml
from invenio_communities.communities.records.models import CommunityMetadata


def dump_communities():
    """Dump communities map of slug -> community id."""
    community_map = {comm.slug: str(comm.id) for comm in CommunityMetadata.query.all()}
    streams_path = str(Path("site/zenodo_rdm/migrator/streams.yaml").absolute())
    streams = {}
    with open(streams_path, "r") as fp:
        streams = yaml.safe_load(fp)
    streams["records"]["load"]["cache"]["communities"] = community_map
    with open(streams_path, "w") as fp:
        yaml.safe_dump(streams, fp, default_flow_style=False)


def invalidate_user_community_roles_cache():
    """Invalidate all users communties roles cache.

    That will trigger the renewal of the cache next time a user visits a community page.
    That might be needed if a user is already logged in while communities are being
    migrated thus new roles are being added in the db.
    """
    from flask_principal import Identity
    from invenio_accounts.models import User
    from invenio_communities.utils import on_membership_change

    users = User.query.all()

    for user in users:
        user_identity = Identity(user.id)
        # delete cache
        on_membership_change(user_identity)
