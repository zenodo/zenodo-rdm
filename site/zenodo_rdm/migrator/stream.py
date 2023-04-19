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
