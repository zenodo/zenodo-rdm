# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""

from invenio_rdm_records.contrib.codemeta import (
    CODEMETA_CUSTOM_FIELDS,
    CODEMETA_CUSTOM_FIELDS_UI,
    CODEMETA_FACETS,
    CODEMETA_NAMESPACE,
)
from invenio_rdm_records.contrib.imprint import (
    IMPRINT_CUSTOM_FIELDS,
    IMPRINT_CUSTOM_FIELDS_UI,
    IMPRINT_NAMESPACE,
)
from invenio_rdm_records.contrib.journal import (
    JOURNAL_CUSTOM_FIELDS,
    JOURNAL_CUSTOM_FIELDS_UI,
    JOURNAL_NAMESPACE,
)
from invenio_rdm_records.contrib.meeting import (
    MEETING_CUSTOM_FIELDS,
    MEETING_CUSTOM_FIELDS_UI,
    MEETING_NAMESPACE,
)
from invenio_rdm_records.contrib.thesis import (
    THESIS_CUSTOM_FIELDS,
    THESIS_CUSTOM_FIELDS_UI,
    THESIS_NAMESPACE,
)

from .community_fields import (
    COMMUNITY_FIELDS,
    COMMUNITY_FIELDS_UI,
    COMMUNITY_NAMESPACES,
)
from .domain_fields import (
    AUDIOVIS_FIELDS,
    AUDIOVIS_FIELDS_UI,
    BIODIV_FIELDS,
    BIODIVERSITY_FIELDS_UI,
)
from .legacy import LEGACY_CUSTOM_FIELDS
from .publishing import PUBLISHING_FIELDS_UI

NAMESPACES = {
    "dwc": "http://rs.tdwg.org/dwc/terms/",
    "gbif-dwc": "http://rs.gbif.org/terms/1.0/",
    "ac": "http://rs.tdwg.org/ac/terms/",
    "openbiodiv": "http://openbiodiv.net/ontology#",
    "obo": "http://purl.obolibrary.org/obo/",
    "dc": "http://purl.org/dc/terms/",
    "legacy": "",
    **CODEMETA_NAMESPACE,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
    **JOURNAL_NAMESPACE,
    **MEETING_NAMESPACE,
    **IMPRINT_NAMESPACE,
    **THESIS_NAMESPACE,
}


CUSTOM_FIELDS = [
    *BIODIV_FIELDS,
    *AUDIOVIS_FIELDS,
    # codemeta,
    *CODEMETA_CUSTOM_FIELDS,
    # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
    # journal
    *JOURNAL_CUSTOM_FIELDS,
    # meeting
    *MEETING_CUSTOM_FIELDS,
    # imprint
    *IMPRINT_CUSTOM_FIELDS,
    # thesis
    *THESIS_CUSTOM_FIELDS,
    # legacy
    *LEGACY_CUSTOM_FIELDS,
]


# hide meeting section from Additional details in landing page
MEETING_CUSTOM_FIELDS_UI["hide_from_landing_page"] = True

# Custom fields UI components
CUSTOM_FIELDS_UI = [
    # codemeta
    CODEMETA_CUSTOM_FIELDS_UI,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
    # publishing information
    PUBLISHING_FIELDS_UI,
    # meeting
    MEETING_CUSTOM_FIELDS_UI,
    # zenodo custom fields
    BIODIVERSITY_FIELDS_UI,
    AUDIOVIS_FIELDS_UI,
]

# Custom fields facets

CUSTOM_FIELDS_FACETS = {
    # **CODEMETA_FACETS,  # TODO enable when fixed (see https://github.com/zenodo/rdm-project/issues/217)
}
