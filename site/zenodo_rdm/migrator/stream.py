# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Migrator stream definitions."""

from invenio_rdm_migrator.streams import StreamDefinition
from invenio_rdm_migrator.streams.communities import CommunityCopyLoad
from invenio_rdm_migrator.streams.records import RDMRecordCopyLoad
from invenio_rdm_migrator.streams.requests import RequestCopyLoad
from invenio_rdm_migrator.streams.users import UserCopyLoad

from .extract import JSONLExtract
from .load import ZenodoFilesLoad
from .transform import (
    ZenodoCommunityTransform,
    ZenodoRecordTransform,
    ZenodoRequestTransform,
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
    load_cls=ZenodoFilesLoad,
)
"""ETL stream for Zenodo to import files."""
