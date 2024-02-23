# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom fields."""
from invenio_i18n import lazy_gettext as _
from invenio_vocabularies.services.custom_fields import VocabularyCF

COMMUNITY_FIELDS_UI = [
    {
        "section": _("Subjects"),
        "fields": [
            dict(
                field="subjects",
                ui_widget="SubjectAutocompleteDropdown",
                props=dict(
                    label="Keywords and subjects",
                    icon="tag",
                    description="The subjects related to the community",
                    placeholder="Search for a subject by name e.g. Psychology ...",
                    autocompleteFrom="api/vocabularies/subjects",
                    autocompleteFromAcceptHeader="application/vnd.inveniordm.v1+json",
                    required=False,
                    multiple=True,
                    clearable=True,
                ),
            )
        ],
    }
]


COMMUNITY_FIELDS = {
    VocabularyCF(
        name="subjects",
        vocabulary_id="subjects",
        multiple=True,
        dump_options=False,
    )
}


COMMUNITY_NAMESPACES = {
    "es": "https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/euroscivoc",
}
