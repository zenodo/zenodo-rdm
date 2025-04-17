# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""

from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.contrib.imprint import IMPRINT_CUSTOM_FIELDS_UI
from invenio_rdm_records.contrib.journal import JOURNAL_CUSTOM_FIELDS_UI
from invenio_rdm_records.contrib.thesis import THESIS_CUSTOM_FIELDS_UI
from invenio_records_resources.services.custom_fields import TextCF

DEPRECATED_THESIS_CUSTOM_FIELDS = [
    TextCF(name="thesis:university"),
]

PUBLISHING_FIELDS_UI = {
    "section": _("Publishing information"),
    "hide_from_landing_page": True,  # hide meeting section from Additional details in landing page
    "fields": [
        # journal
        *JOURNAL_CUSTOM_FIELDS_UI["fields"],
        # imprint
        *IMPRINT_CUSTOM_FIELDS_UI["fields"],
        # thesis
        *THESIS_CUSTOM_FIELDS_UI["fields"],
    ],
}
