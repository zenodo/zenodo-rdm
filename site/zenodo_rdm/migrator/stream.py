# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Migrator stream definitions."""

from invenio_rdm_migrator.streams import StreamDefinition
from invenio_rdm_migrator.streams.awards import ExistingAwardsLoad
from invenio_rdm_migrator.streams.communities import CommunityCopyLoad
from invenio_rdm_migrator.streams.files import ExistingFilesLoad
from invenio_rdm_migrator.streams.funders import ExistingFundersLoad
from invenio_rdm_migrator.streams.oauth import (
    OAuthClientCopyLoad,
    OAuthRemoteTokenTransform,
    OAuthServerCopyLoad,
    OAuthServerTokenTransform,
)
from invenio_rdm_migrator.streams.records import RDMRecordCopyLoad
from invenio_rdm_migrator.streams.requests import RequestCopyLoad
from invenio_rdm_migrator.streams.users import UserCopyLoad


from .extract import JSONLExtract

from .load import ZenodoTransactionLoad
from .transform import (
    ZenodoCommunityTransform,
    ZenodoRecordTransform,
    ZenodoRequestTransform,
    ZenodoTransactionGroupTransform,
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
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo to RDM drafts."""

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

OAuthClientStreamDefinition = StreamDefinition(
    name="oauthclient",
    # only the tokens need loading from file, the rest are existing data
    extract_cls=JSONLExtract,
    # will use transform the tokens and forward on the rest
    transform_cls=OAuthRemoteTokenTransform,
    load_cls=OAuthClientCopyLoad,
)
"""ETL stream for Zenodo to import OAutch clients related information."""

OAuthServerStreamDefinition = StreamDefinition(
    name="oauthserver",
    # only the tokens need loading from file, the rest are existing data
    extract_cls=JSONLExtract,
    # will use transform the tokens and forward on the rest
    transform_cls=OAuthServerTokenTransform,
    load_cls=OAuthServerCopyLoad,
)
"""ETL stream for Zenodo to import OAutch clients related information."""

ActionStreamDefinition = StreamDefinition(
    name="action",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoTransactionGroupTransform,
    load_cls=ZenodoTransactionLoad,
)
"""ETL stream for Zenodo to import awards."""
