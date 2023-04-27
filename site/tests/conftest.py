# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures."""

from collections import namedtuple

import pytest
from flask_security import login_user
from flask_security.utils import hash_password
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access, system_identity
from invenio_accounts.models import Role
from invenio_accounts.testutils import login_user_via_session
from invenio_administration.permissions import administration_access_action
from invenio_app.factory import create_api as _create_api
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary

from zenodo_rdm.permissions import ZenodoRDMRecordPermissionPolicy


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["RDM_PERMISSION_POLICY"] = ZenodoRDMRecordPermissionPolicy
    app_config["REST_CSRF_ENABLED"] = False
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


RunningApp = namedtuple(
    "RunningApp",
    [
        "app",
        "superuser_identity",
        "location",
        "cache",
        "resource_type_v",
    ],
)


@pytest.fixture
def running_app(
    app,
    superuser_identity,
    location,
    cache,
    resource_type_v,
):
    """Fixture provides an app with the typically needed db data loaded.

    All of these fixtures are often needed together, so collecting them
    under a semantic umbrella makes sense.
    """
    return RunningApp(
        app,
        superuser_identity,
        location,
        cache,
        resource_type_v,
    )


@pytest.fixture
def test_app(running_app):
    """Get current app."""
    return running_app.app


@pytest.fixture()
def users(app, db):
    """Create example users."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        user1 = datastore.create_user(
            email="info@zenodo.org",
            password=hash_password("password"),
            active=True,
        )

    db.session.commit()
    return [user1]


@pytest.fixture()
def client_with_login(client, users):
    """Log in a user to the client."""
    user = users[0]
    login_user(user)
    login_user_via_session(client, email=user.email)
    return client


@pytest.fixture(scope="module")
def resource_type_v(app):
    """Resource type vocabulary record."""
    vocabulary_service.create_type(system_identity, "resourcetypes", "rsrct")
    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "image-photo",
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )
    Vocabulary.index.refresh()
    return vocab


@pytest.fixture()
def minimal_record():
    """Minimal record data as dict coming from the external world."""
    return {
        "pids": {},
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {
            "enabled": False,  # Most tests don't care about files
        },
        "metadata": {
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Brown",
                        "given_name": "Troy",
                        "type": "personal",
                    }
                },
            ],
            "publication_date": "2020-06-01",
            "publisher": "Acme Inc",
            "resource_type": {"id": "image-photo"},
            "title": "A Romans story",
        },
    }


@pytest.fixture()
def minimal_community():
    """Data for a minimal community."""
    return {
        "slug": "blr",
        "access": {
            "visibility": "public",
        },
        "metadata": {
            "title": "Biodiversity Literature Repository",
            "type": {"id": "topic"},
        },
    }


@pytest.fixture()
def test_user(UserFixture, app, db):
    """User meant to test permissions."""
    u = UserFixture(
        email="testuser@inveniosoftware.org",
        password="testuser",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def uploader(UserFixture, app, db):
    """Uploader."""
    u = UserFixture(
        email="uploader@inveniosoftware.org",
        password="uploader",
    )
    u.create(app, db)
    return u


@pytest.fixture()
def community_owner(UserFixture, app, db):
    """Community owner."""
    u = UserFixture(
        email="community_owner@inveniosoftware.org",
        password="community_owner",
    )
    u.create(app, db)
    return u


@pytest.fixture(scope="session")
def headers():
    """Default headers for making requests."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
    }


@pytest.fixture()
def superuser_role_need(db):
    """Store 1 role with 'superuser-access' ActionNeed.

    WHY: This is needed because expansion of ActionNeed is
         done on the basis of a User/Role being associated with that Need.
         If no User/Role is associated with that Need (in the DB), the
         permission is expanded to an empty list.
    """
    role = Role(name="superuser-access")
    db.session.add(role)

    action_role = ActionRoles.create(action=superuser_access, role=role)
    db.session.add(action_role)
    db.session.commit()

    return action_role.need


@pytest.fixture()
def superuser_identity(admin, superuser_role_need):
    """Superuser identity fixture."""
    identity = admin.identity
    identity.provides.add(superuser_role_need)
    return identity


@pytest.fixture()
def admin_role_need(db):
    """Store 1 role with 'superuser-access' ActionNeed.

    WHY: This is needed because expansion of ActionNeed is
         done on the basis of a User/Role being associated with that Need.
         If no User/Role is associated with that Need (in the DB), the
         permission is expanded to an empty list.
    """
    role = Role(name="administration-access")
    db.session.add(role)

    action_role = ActionRoles.create(action=administration_access_action, role=role)
    db.session.add(action_role)
    db.session.commit()

    return action_role.need


@pytest.fixture()
def admin(UserFixture, app, db, admin_role_need):
    """Admin user for requests."""
    u = UserFixture(
        email="admin@inveniosoftware.org",
        password="admin",
    )
    u.create(app, db)

    datastore = app.extensions["security"].datastore
    _, role = datastore._prepare_role_modify_args(u.user, "administration-access")

    datastore.add_role_to_user(u.user, role)
    db.session.commit()
    return u


@pytest.fixture()
def community_type_record(superuser_identity):
    """Creates and retrieves community type records."""
    vocabulary_service.create_type(superuser_identity, "communitytypes", "comtyp")
    record = vocabulary_service.create(
        identity=superuser_identity,
        data={
            "id": "topic",
            "title": {"en": "Topic"},
            "type": "communitytypes",
        },
    )
    Vocabulary.index.refresh()  # Refresh the index

    return record


def _community_get_or_create(community_dict, identity):
    """Util to get or create community, to avoid duplicate error."""
    slug = community_dict["slug"]
    try:
        c = current_communities.service.record_cls.pid.resolve(slug)
    except PIDDoesNotExistError:
        c = current_communities.service.create(
            identity,
            community_dict,
        )
        Community.index.refresh()
    return c


@pytest.fixture()
def community(running_app, community_type_record, community_owner, minimal_community):
    """Get the current RDM records service."""
    return _community_get_or_create(minimal_community, community_owner.identity)


@pytest.fixture()
def community_with_uploader_owner(
    running_app, community_type_record, uploader, minimal_community
):
    """Create a community with an uploader owner."""
    return _community_get_or_create(minimal_community, uploader.identity)
