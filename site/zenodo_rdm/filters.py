# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Filters to be used in the Jinja templates."""

from invenio_records.dictutils import dict_lookup


def is_blr_related_record(record):
    """Check if we need to display related records for this record."""
    valid_types = [
        "Figure",
        "Taxonomic treatment",
        "Book chapter",
        "Journal article",
        "Drawing",
    ]

    try:
        slug = dict_lookup(record, "expanded.parent.communities.default.slug")
        resource_type = dict_lookup(record, "metadata.resource_type.title.en")
        is_valid_type = resource_type in valid_types

        if slug == "biosyslit" and is_valid_type:
            return True

        return False
    except KeyError:
        return False
