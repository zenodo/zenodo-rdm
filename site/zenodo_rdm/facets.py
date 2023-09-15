# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Zenodo communities facets."""

from invenio_i18n import gettext as _
from invenio_records_resources.services.records.facets import TermsFacet
from invenio_vocabularies.contrib.affiliations.facets import AffiliationsLabels
from invenio_vocabularies.contrib.funders.facets import FundersLabels

funder = TermsFacet(
    field="metadata.funding.funder.id",
    label=_("Funders"),
    value_labels=FundersLabels("funders"),
)

organization = TermsFacet(
    field="metadata.organizations.id",
    label=_("Organizations"),
    value_labels=AffiliationsLabels("affiliations"),
)

visibility = TermsFacet(
    field="access.visibility",
    label=_("Visibility"),
    value_labels={
        "restricted": _("Restricted"),
    },
)
