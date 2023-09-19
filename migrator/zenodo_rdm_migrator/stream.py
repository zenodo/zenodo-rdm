# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Migrator stream definitions."""

from invenio_rdm_migrator.extract import JSONLExtract
from invenio_rdm_migrator.load.postgresql.transactions import PostgreSQLTx
from invenio_rdm_migrator.streams import StreamDefinition
from invenio_rdm_migrator.streams.affiliations import ExistingAffiliationsLoad
from invenio_rdm_migrator.streams.names import ExistingNamesLoad
from invenio_rdm_migrator.streams.awards import ExistingAwardsLoad
from invenio_rdm_migrator.streams.communities import CommunityCopyLoad
from invenio_rdm_migrator.streams.files import ExistingFilesLoad
from invenio_rdm_migrator.streams.funders import ExistingFundersLoad
from invenio_rdm_migrator.streams.github import (
    ExistingGitHubRepositoriesCopyLoad,
    ExistingWebhookEventsCopyLoad,
    GitHubReleasesCopyLoad,
    GitHubReleaseTransform,
)
from invenio_rdm_migrator.streams.oauth import (
    OAuthClientCopyLoad,
    OAuthServerClientCopyLoad,
    OAuthServerClientTransform,
    OAuthServerTokenCopyLoad,
    OAuthServerTokenTransform,
)
from invenio_rdm_migrator.streams.records import (
    RDMDraftCopyLoad,
    RDMRecordCopyLoad,
    RDMVersionStateCopyLoad,
)
from invenio_rdm_migrator.streams.requests import RequestCopyLoad
from invenio_rdm_migrator.streams.users import UserCopyLoad

from .extract import KafkaExtract
from .transform import (
    ZenodoCommunityTransform,
    ZenodoRecordTransform,
    ZenodoRequestTransform,
    ZenodoTxTransform,
    ZenodoUserTransform,
)

CommunitiesStreamDefinition = StreamDefinition(
    name="communities",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoCommunityTransform,
    load_cls=CommunityCopyLoad,
)
"""ETL stream for Zenodo to RDM communities."""

RecordStreamDefinition = StreamDefinition(
    name="records",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRecordTransform,
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo to RDM records."""

DraftStreamDefinition = StreamDefinition(
    name="drafts",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRecordTransform,
    load_cls=RDMDraftCopyLoad,
)
"""ETL stream for Zenodo to RDM drafts."""

DeletedRecordStreamDefinition = StreamDefinition(
    name="deleted_records",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRecordTransform,
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo deleted records."""

VersionStateStreamDefinition = StreamDefinition(
    name="version_state",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRecordTransform,
    load_cls=RDMVersionStateCopyLoad,
)
"""ETL stream for version state."""

UserStreamDefinition = StreamDefinition(
    name="users",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoUserTransform,
    load_cls=UserCopyLoad,
)
"""ETL stream for Zenodo to import users."""

RequestStreamDefinition = StreamDefinition(
    name="requests",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoRequestTransform,
    load_cls=RequestCopyLoad,
)
"""ETL stream for Zenodo to import users."""

FilesStreamDefinition = StreamDefinition(
    name="files",
    extract_cls=None,  # will use IdentityExtract
    transform_cls=None,  # will use IdentityTransform
    load_cls=ExistingFilesLoad,
)
"""ETL stream for Zenodo to import files."""

FundersStreamDefinition = StreamDefinition(
    name="funders",
    extract_cls=None,  # will use IdentityExtract
    transform_cls=None,  # will use IdentityTransform
    load_cls=ExistingFundersLoad,
)
"""ETL stream for Zenodo to import funders."""

AwardsStreamDefinition = StreamDefinition(
    name="awards",
    extract_cls=None,  # will use IdentityExtract
    transform_cls=None,  # will use IdentityTransform
    load_cls=ExistingAwardsLoad,
)
"""ETL stream for Zenodo to import awards."""

AffiliationsStreamDefinition = StreamDefinition(
    name="affiliations",
    extract_cls=None,  # will use IdentityExtract
    transform_cls=None,  # will use IdentityTransform
    load_cls=ExistingAffiliationsLoad,
)
"""ETL stream for Zenodo to import affiliations."""

NamesStreamDefinition = StreamDefinition(
    name="names",
    extract_cls=None,  # will use IdentityExtract
    transform_cls=None,  # will use IdentityTransform
    load_cls=ExistingNamesLoad,
)
"""ETL stream for Zenodo to import names."""


OAuthClientStreamDefinition = StreamDefinition(
    name="oauthclient",
    extract_cls=None,
    transform_cls=None,
    load_cls=OAuthClientCopyLoad,
)
"""ETL stream for Zenodo to import OAutch clients related information."""

OAuthServerClientStreamDefinition = StreamDefinition(
    name="oauthserver_clients",
    extract_cls=JSONLExtract,
    transform_cls=OAuthServerClientTransform,
    load_cls=OAuthServerClientCopyLoad,
)
"""ETL stream for Zenodo to import OAutch clients related information."""

OAuthServerTokenStreamDefinition = StreamDefinition(
    name="oauthserver_tokens",
    extract_cls=JSONLExtract,
    transform_cls=OAuthServerTokenTransform,
    load_cls=OAuthServerTokenCopyLoad,
)
"""ETL stream for Zenodo to import OAutch clients related information."""

WebhookEventsStreamDefinition = StreamDefinition(
    name="webhook_events",
    extract_cls=None,
    transform_cls=None,
    load_cls=ExistingWebhookEventsCopyLoad,
)
"""ETL stream for Zenodo to import webhook events."""

GitHubRepositoriesStreamDefinition = StreamDefinition(
    name="github_repositories",
    extract_cls=None,
    transform_cls=None,
    load_cls=ExistingGitHubRepositoriesCopyLoad,
)
"""ETL stream for Zenodo to import GitHub repositories."""

GitHubReleasesStreamDefinition = StreamDefinition(
    name="github_releases",
    extract_cls=JSONLExtract,
    transform_cls=GitHubReleaseTransform,
    load_cls=GitHubReleasesCopyLoad,
)
"""ETL stream for Zenodo to import GitHub releases."""

ActionStreamDefinition = StreamDefinition(
    name="action",
    extract_cls=KafkaExtract,
    transform_cls=ZenodoTxTransform,
    load_cls=PostgreSQLTx,
)
"""ETL stream for Zenodo to import awards."""
