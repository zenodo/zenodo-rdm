# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2024 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""


from flask import current_app
from invenio_search import current_search_client
from invenio_search.utils import build_alias_name, build_index_name


def get_percolator_index(record_cls):
    """Build the percolator index alias name for a given record class."""
    prefix = current_app.config.get("MODERATION_PERCOLATOR_INDEX_PREFIX")
    combined_index = f"{prefix}-{record_cls.index._name}"
    return build_alias_name(combined_index, app=current_app)


def create_percolator_index(record_cls):
    """Create mappings with the percolator field for moderation queries.

    This function creates a new Elasticsearch index for percolator queries by copying
    the settings and mappings from an existing record index and adding specific
    percolator mappings.
    """
    # Build the name for the new percolator index, using a prefix and the record's index name
    combined_index_name = f"{current_app.config.get('MODERATION_PERCOLATOR_INDEX_PREFIX')}-{record_cls.index._name}"
    percolator_index = build_index_name(combined_index_name, app=current_app)

    # Get the current mapping for the record index to copy its structure
    record_index = build_alias_name(record_cls.index._name)
    record_mapping = current_search_client.indices.get_mapping(index=record_index)
    assert len(record_mapping) == 1
    # Extract the mappings from the record index and store in `percolator_mappings`
    percolator_mappings = list(record_mapping.values())[0]["mappings"]

    # Add specific properties for percolator fields from the app configuration
    percolator_mappings["properties"].update(
        current_app.config.get("MODERATION_PERCOLATOR_MAPPING")["properties"]
    )

    # Retrieve the current settings of the record index to copy them to the percolator index
    record_settings = list(
        current_search_client.indices.get_settings(index=record_index).values()
    )[0]["settings"]["index"]

    percolator_settings = {
        "index": {
            "query": {
                "default_field": record_settings.get("query", {}).get(
                    "default_field", []
                )
            }
        },
        "analysis": record_settings.get("analysis", {}),
    }

    if not current_search_client.indices.exists(percolator_index):
        try:
            current_search_client.indices.create(
                index=percolator_index,
                body={
                    "settings": percolator_settings,
                    "mappings": {**percolator_mappings},
                },
            )
        except Exception as e:
            current_app.logger.exception(e)


def index_percolate_query(record_cls, query_string, active=True, score=1, notes=None):
    """Index a percolate query."""
    try:
        current_search_client.index(
            index=get_percolator_index(record_cls),
            body={
                "query": {"query_string": {"query": query_string}},
                "active": active,
                "score": score,
                "notes": notes,
            },
        )
    except Exception as e:
        current_app.logger.exception(e)
