# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures."""

from collections import namedtuple

import pytest
from flask_security.utils import hash_password
from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access, system_identity
from invenio_accounts.models import Role
from invenio_administration.permissions import administration_access_action
from invenio_app import factory as app_factory
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_communities.generators import CommunityRoleNeed
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.cli import create_records_custom_field
from invenio_rdm_records.services.pids import providers
from invenio_records_resources.proxies import current_service_registry
from invenio_vocabularies.contrib.awards.api import Award
from invenio_vocabularies.contrib.funders.api import Funder
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary

from zenodo_rdm.api import ZenodoRDMDraft, ZenodoRDMRecord
from zenodo_rdm.custom_fields import CUSTOM_FIELDS, CUSTOM_FIELDS_UI, NAMESPACES
from zenodo_rdm.legacy.requests.record_upgrade import LegacyRecordUpgrade
from zenodo_rdm.legacy.resources import record_serializers
from zenodo_rdm.permissions import ZenodoRDMRecordPermissionPolicy

from .fake_datacite_client import FakeDataCiteClient


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["REST_CSRF_ENABLED"] = False
    app_config["DATACITE_ENABLED"] = True
    app_config["RDM_PERSISTENT_IDENTIFIER_PROVIDERS"] = [
        # DataCite DOI provider with fake client
        providers.DataCitePIDProvider(
            "datacite",
            client=FakeDataCiteClient("datacite", config_prefix="DATACITE"),
            label=("DOI"),
        ),
        # DOI provider for externally managed DOIs
        providers.ExternalPIDProvider(
            "external",
            "doi",
            validators=[providers.BlockedPrefixes(config_names=["DATACITE_PREFIX"])],
            label=("DOI"),
        ),
        # OAI identifier
        providers.OAIPIDProvider(
            "oai",
            label=("OAI ID"),
        ),
    ]
    app_config["DATACITE_PREFIX"] = "10.5281"
    app_config["DATACITE_FORMAT"] = "{prefix}/zenodo.{id}"
    app_config["RDM_NAMESPACES"] = NAMESPACES
    app_config["RDM_CUSTOM_FIELDS"] = CUSTOM_FIELDS
    app_config["RDM_CUSTOM_FIELDS_UI"] = CUSTOM_FIELDS_UI  #  UI components
    app_config["RDM_PERMISSION_POLICY"] = ZenodoRDMRecordPermissionPolicy
    app_config["RDM_RECORD_CLS"] = ZenodoRDMRecord
    app_config["RDM_DRAFT_CLS"] = ZenodoRDMDraft
    app_config["RDM_RECORDS_SERIALIZERS"] = record_serializers
    app_config["REQUESTS_REGISTERED_TYPES"] = [LegacyRecordUpgrade()]
    # TODO this is a temporary fix for https://github.com/zenodo/zenodo-rdm/issues/380
    app_config["ACCOUNTS_USERINFO_HEADERS"] = False
    app_config["BLUEPRINTS_URL_PREFIXES"] = {
        "invenio_files_rest": "/legacy-files",
    }
    # OpenAIRE configs
    app_config["OPENAIRE_PORTAL_URL"] = "https://explore.openaire.eu"
    app_config["OPENAIRE_COMMUNITIES"] = {
        "foo": {
            "name": "Foo Optimization Organization",
            "communities": [
                "c1",
                "c2",
            ],
            "types": {
                "software": [
                    {"id": "foo:t1", "name": "Foo sft type one"},
                    {"id": "foo:t2", "name": "Foo sft type two"},
                ],
                "other": [
                    {"id": "foo:t4", "name": "Foo other type four"},
                    {"id": "foo:t5", "name": "Foo other type five"},
                ],
            },
        },
        "bar": {
            "name": "Bar Association Resources",
            "communities": ["c3", "c1"],
            "types": {
                "software": [
                    {"id": "bar:t3", "name": "Bar sft type three"},
                ],
                "other": [
                    {"id": "bar:t6", "name": "Bar other type six"},
                ],
            },
        },
    }

    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture."""
    return app_factory.create_app


RunningApp = namedtuple(
    "RunningApp",
    [
        "app",
        "superuser_identity",
        "location",
        "cache",
        "resource_type_v",
        "languages_type",
        "funders_v",
        "awards_v",
        "licenses_v",
        "contributors_role_v",
        "description_type_v",
        "relation_type_v",
        "initialise_custom_fields",
    ],
)


@pytest.fixture
def running_app(
    app,
    superuser_identity,
    location,
    cache,
    resource_type_v,
    languages_type,
    funders_v,
    awards_v,
    licenses_v,
    contributors_role_v,
    description_type_v,
    relation_type_v,
    initialise_custom_fields,
):
    """This fixture provides an app with the typically needed db data loaded.

    All of these fixtures are often needed together, so collecting them
    under a semantic umbrella makes sense.
    """
    return RunningApp(
        app,
        superuser_identity,
        location,
        cache,
        resource_type_v,
        languages_type,
        funders_v,
        awards_v,
        licenses_v,
        contributors_role_v,
        description_type_v,
        relation_type_v,
        initialise_custom_fields,
    )


@pytest.fixture
def test_app(running_app):
    """Get current app."""
    return running_app.app


@pytest.fixture(scope="session")
def headers():
    """Default headers for making requests."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
    }


@pytest.fixture(scope="session")
def files_headers():
    """Default headers for making file upload requests."""
    return {
        "content-type": "application/octet-stream",
        "accept": "application/json",
    }


@pytest.fixture()
def users(app, db):
    """Create example users."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        user1 = datastore.create_user(
            email="info@zsenodo.org",
            password=hash_password("password"),
            active=True,
        )
        user2 = datastore.create_user(
            email="test@zsenodo.org",
            password=hash_password("password"),
            active=True,
        )

    db.session.commit()
    return [user1, user2]


@pytest.fixture()
def client_with_login(client, uploader):
    """Log in a user to the client."""
    return uploader.api_login(client)


@pytest.fixture(scope="module")
def resource_type_type(app):
    """Resource type vocabulary type."""
    return vocabulary_service.create_type(system_identity, "resourcetypes", "rsrct")


@pytest.fixture(scope="module")
def resource_type_v(app, resource_type_type):
    """Resource type vocabulary record."""
    vocabulary_service.create(
        system_identity,
        {
            "id": "dataset",
            "icon": "table",
            "props": {
                "csl": "dataset",
                "datacite_general": "Dataset",
                "datacite_type": "",
                "openaire_resourceType": "21",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/Dataset",
                "subtype": "",
                "type": "dataset",
            },
            "title": {"en": "Dataset"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {  # create base resource type
            "id": "image",
            "props": {
                "csl": "figure",
                "datacite_general": "Image",
                "datacite_type": "",
                "openaire_resourceType": "25",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantic/other",
                "schema.org": "https://schema.org/ImageObject",
                "subtype": "",
                "type": "image",
            },
            "icon": "chart bar outline",
            "title": {"en": "Image"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {
            "id": "publication-book",
            "icon": "file alternate",
            "props": {
                "csl": "book",
                "datacite_general": "Text",
                "datacite_type": "Book",
                "openaire_resourceType": "2",
                "openaire_type": "publication",
                "eurepo": "info:eu-repo/semantics/book",
                "schema.org": "https://schema.org/Book",
                "subtype": "publication-book",
                "type": "publication",
            },
            "title": {"en": "Book", "de": "Buch"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {
            "id": "presentation",
            "icon": "group",
            "props": {
                "csl": "speech",
                "datacite_general": "Text",
                "datacite_type": "Presentation",
                "openaire_resourceType": "0004",
                "openaire_type": "publication",
                "eurepo": "info:eu-repo/semantics/lecture",
                "schema.org": "https://schema.org/PresentationDigitalDocument",
                "subtype": "",
                "type": "presentation",
            },
            "title": {"en": "Presentation", "de": "Präsentation"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {
            "id": "publication",
            "icon": "file alternate",
            "props": {
                "csl": "report",
                "datacite_general": "Text",
                "datacite_type": "",
                "openaire_resourceType": "0017",
                "openaire_type": "publication",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/CreativeWork",
                "subtype": "",
                "type": "publication",
            },
            "title": {"en": "Publication", "de": "Publikation"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {
            "id": "image-photo",
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
            "props": {
                "csl": "graphic",
                "datacite_general": "Image",
                "datacite_type": "Photo",
                "openaire_resourceType": "0025",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/Photograph",
                "subtype": "image-photo",
                "type": "image",
            },
        },
    )

    vocabulary_service.create(
        system_identity,
        {
            "id": "software",
            "icon": "code",
            "type": "resourcetypes",
            "props": {
                "csl": "software",
                "datacite_general": "Software",
                "datacite_type": "",
                "openaire_resourceType": "0029",
                "openaire_type": "software",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/SoftwareSourceCode",
                "subtype": "",
                "type": "software",
            },
            "title": {"en": "Software", "de": "Software"},
            "tags": ["depositable", "linkable"],
        },
    )

    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "other",
            "icon": "asterisk",
            "type": "resourcetypes",
            "props": {
                "csl": "article",
                "datacite_general": "Other",
                "datacite_type": "",
                "openaire_resourceType": "0020",
                "openaire_type": "other",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/CreativeWork",
                "subtype": "",
                "type": "other",
            },
            "title": {
                "en": "Other",
                "de": "Sonstige",
            },
            "tags": ["depositable", "linkable"],
        },
    )

    Vocabulary.index.refresh()

    return vocab


@pytest.fixture(scope="module")
def languages_type(app):
    """Lanuage vocabulary type."""
    return vocabulary_service.create_type(system_identity, "languages", "lng")


@pytest.fixture(scope="module")
def languages_v(app, languages_type):
    """Language vocabulary record."""
    vocabulary_service.create(
        system_identity,
        {
            "id": "dan",
            "title": {
                "en": "Danish",
                "da": "Dansk",
            },
            "props": {"alpha_2": "da"},
            "tags": ["individual", "living"],
            "type": "languages",
        },
    )

    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "eng",
            "title": {
                "en": "English",
                "da": "Engelsk",
            },
            "tags": ["individual", "living"],
            "type": "languages",
        },
    )

    Vocabulary.index.refresh()

    return vocab


@pytest.fixture(scope="module")
def funders_v(app, funder_data):
    """Funder vocabulary record."""
    funders_service = current_service_registry.get("funders")
    funder = funders_service.create(
        system_identity,
        funder_data,
    )

    Funder.index.refresh()

    return funder


@pytest.fixture(scope="module")
def awards_v(app, funders_v):
    """Funder vocabulary record."""
    awards_service = current_service_registry.get("awards")
    award = awards_service.create(
        system_identity,
        {
            "id": "00rbzpz17::755021",
            "identifiers": [
                {
                    "identifier": "https://cordis.europa.eu/project/id/755021",
                    "scheme": "url",
                }
            ],
            "number": "755021",
            "title": {
                "en": (
                    "Personalised Treatment For Cystic Fibrosis Patients With "
                    "Ultra-rare CFTR Mutations (and beyond)"
                ),
            },
            "funder": {"id": "00rbzpz17"},
            "acronym": "HIT-CF",
            "program": "H2020",
        },
    )

    Award.index.refresh()

    return award


@pytest.fixture(scope="module")
def licenses(app):
    """Licenses vocabulary type."""
    return vocabulary_service.create_type(system_identity, "licenses", "lic")


@pytest.fixture(scope="module")
def licenses_v(app, licenses):
    """Licenses vocabulary record."""
    cc_zero = vocabulary_service.create(
        system_identity,
        {
            "id": "cc0-1.0",
            "title": {
                "en": "Creative Commons Zero v1.0 Universal",
            },
            "description": {
                "en": (
                    "CC0 waives copyright interest in a work you've created and "
                    "dedicates it to the world-wide public domain. Use CC0 to opt out "
                    "of copyright entirely and ensure your work has the widest reach."
                ),
            },
            "icon": "cc-cc0-icon",
            "tags": ["recommended", "all", "data", "software"],
            "props": {
                "url": "https://creativecommons.org/publicdomain/zero/1.0/legalcode",
                "scheme": "spdx",
                "osi_approved": "",
            },
            "type": "licenses",
        },
    )
    cc_by = vocabulary_service.create(
        system_identity,
        {
            "id": "cc-by-4.0",
            "title": {
                "en": "Creative Commons Attribution 4.0 International",
            },
            "description": {
                "en": (
                    "The Creative Commons Attribution license allows re-distribution "
                    "and re-use of a licensed work on the condition that the creator "
                    "is appropriately credited."
                ),
            },
            "icon": "cc-by-icon",
            "tags": ["recommended", "all", "data"],
            "props": {
                "url": "https://creativecommons.org/licenses/by/4.0/legalcode",
                "scheme": "spdx",
                "osi_approved": "",
            },
            "type": "licenses",
        },
    )

    Vocabulary.index.refresh()

    return [cc_zero, cc_by]


@pytest.fixture(scope="module")
def contributors_role_type(app):
    """Contributor role vocabulary type."""
    return vocabulary_service.create_type(system_identity, "contributorsroles", "cor")


@pytest.fixture(scope="module")
def contributors_role_v(app, contributors_role_type):
    """Contributor role vocabulary record."""
    vocabulary_service.create(
        system_identity,
        {
            "id": "other",
            "props": {"datacite": "Other"},
            "title": {"en": "Other"},
            "type": "contributorsroles",
        },
    )

    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "datacurator",
            "props": {"datacite": "DataCurator"},
            "title": {"en": "Data curator", "de": "DatenkuratorIn"},
            "type": "contributorsroles",
        },
    )

    vocabulary_service.create(
        system_identity,
        {
            "id": "supervisor",
            "props": {"datacite": "Supervisor"},
            "title": {"en": "Supervisor"},
            "type": "contributorsroles",
        },
    )

    Vocabulary.index.refresh()

    return vocab


@pytest.fixture(scope="module")
def description_type(app):
    """Title vocabulary type."""
    return vocabulary_service.create_type(system_identity, "descriptiontypes", "dty")


@pytest.fixture(scope="module")
def description_type_v(app, description_type):
    """Title Type vocabulary record."""
    vocabulary_service.create(
        system_identity,
        {
            "id": "methods",
            "title": {"en": "Methods"},
            "props": {"datacite": "Methods"},
            "type": "descriptiontypes",
        },
    )

    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "other",
            "title": {"en": "Other"},
            "props": {"datacite": "Other"},
            "type": "descriptiontypes",
        },
    )

    Vocabulary.index.refresh()

    return vocab


@pytest.fixture(scope="module")
def relation_type(app):
    """Relation type vocabulary type."""
    return vocabulary_service.create_type(system_identity, "relationtypes", "rlt")


@pytest.fixture(scope="module")
def relation_type_v(app, relation_type):
    """Relation type vocabulary record."""
    vocabulary_service.create(
        system_identity,
        {
            "id": "iscitedby",
            "props": {"datacite": "IsCitedBy"},
            "title": {"en": "Is cited by"},
            "type": "relationtypes",
        },
    )

    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "cites",
            "props": {"datacite": "Cites"},
            "title": {"en": "Cites", "de": "Zitiert"},
            "type": "relationtypes",
        },
    )

    Vocabulary.index.refresh()

    return vocab


@pytest.fixture(scope="function")
def initialise_custom_fields(app, db, location, cli_runner):
    """Fixture initialises custom fields."""
    return cli_runner(create_records_custom_field)


@pytest.fixture()
def minimal_record():
    """Minimal record data as dict coming from the external world."""
    return {
        "pids": {},
        "access": {
            "record": "public",
            "files": "restricted",
        },
        "files": {
            "enabled": True,  # Most tests don't care about files
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
            "review_policy": "open",
        },
        "metadata": {
            "title": "Biodiversity Literature Repository",
            "type": {"id": "topic"},
        },
    }


@pytest.fixture()
def minimal_community2():
    """Data for a minimal community two."""
    return {
        "slug": "rdm",
        "access": {"visibility": "public", "review_policy": "open"},
        "metadata": {"title": "Research Data Management", "type": {"id": "topic"}},
    }


@pytest.fixture()
def ec_funded_community_data():
    """Data for a 'ecfunded' community."""
    return {
        "slug": "ecfunded",
        "access": {"visibility": "public", "review_policy": "open"},
        "metadata": {
            "title": "European Commission Funded Research (OpenAIRE)",
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
def superuser(UserFixture, app, db, superuser_role_need):
    """Superuser."""
    u = UserFixture(
        email="superuser@inveniosoftware.org",
        password="superuser",
    )
    u.create(app, db)

    datastore = app.extensions["security"].datastore
    _, role = datastore._prepare_role_modify_args(u.user, "superuser-access")

    datastore.add_role_to_user(u.user, role)
    db.session.commit()
    return u


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
def community2(running_app, community_type_record, community_owner, minimal_community2):
    """Get the current RDM records service."""
    return _community_get_or_create(minimal_community2, community_owner.identity)


@pytest.fixture()
def community_with_uploader_owner(
    running_app, community_type_record, uploader, minimal_community2
):
    """Create a community with an uploader owner."""
    return _community_get_or_create(minimal_community2, uploader.identity)


@pytest.fixture()
def ec_funded_community(
    running_app, community_type_record, community_owner, ec_funded_community_data
):
    """Get the current RDM records service."""
    return _community_get_or_create(ec_funded_community_data, community_owner.identity)


@pytest.fixture(scope="module")
def funder_data():
    """Implements a funder's data."""
    return {
        "id": "00rbzpz17",
        "identifiers": [
            {
                "identifier": "00rbzpz17",
                "scheme": "ror",
            },
            {"identifier": "10.13039/501100001665", "scheme": "doi"},
        ],
        "name": "Agence Nationale de la Recherche",
        "title": {
            "fr": "National Agency for Research",
        },
        "country": "FR",
    }
