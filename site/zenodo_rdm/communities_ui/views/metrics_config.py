# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Community metrics config."""

THEME_METRICS_QUERY = {
    "horizon": {
        "total_grants": {
            "name": "total_grants",
            "type": "cardinality",
            "kwargs": {"field": "metadata.funding.award.id"},
        },
        "total_data": {
            "name": "total_data",
            "type": "sum",
            "kwargs": {"field": "files.totalbytes"},
        },
    },
    "biosyslit": {
        "total_views": {
            "name": "total_views",
            "type": "sum",
            "kwargs": {"field": "stats.all_versions.unique_views"},
        },
        "total_downloads": {
            "name": "total_downloads",
            "type": "sum",
            "kwargs": {"field": "stats.all_versions.unique_downloads"},
        },
        "resource_types": {
            "name": "resource_types",
            "type": "filters",
            "kwargs": {
                "filters": {
                    "publications": {
                        "terms": {
                            "metadata.resource_type.id": [
                                "publication-book",
                                "publication-article",
                                "publication-section",
                                "publication-datamanagementplan",
                            ]
                        }
                    },
                    "images": {"prefix": {"metadata.resource_type.id": "image"}},
                    "tables": {"term": {"metadata.resource_type.id": "dataset"}},
                    "treatments": {
                        "term": {
                            "metadata.resource_type.id": "publication-taxonomictreatment"
                        }
                    },
                },
                "aggs": {
                    "openness": {
                        "filter": {
                            "term": {
                                "access.files": "public",
                            },
                        },
                    },
                },
            },
        },
    },
}

THEME_METRICS = {
    "horizon": {"total_data": "total_data.value", "total_grants": "total_grants.value"},
    "biosyslit": {
        "total_views": "total_views.value",
        "total_downloads": "total_downloads.value",
        "publications": "resource_types.buckets.publications.doc_count",
        "images": "resource_types.buckets.images.doc_count",
        "tables": "resource_types.buckets.tables.doc_count",
        "treatments": "resource_types.buckets.treatments.doc_count",
        "open_publications": "resource_types.buckets.publications.openness.doc_count",
        "open_images": "resource_types.buckets.images.openness.doc_count",
        "open_tables": "resource_types.buckets.tables.openness.doc_count",
        "open_treatments": "resource_types.buckets.treatments.openness.doc_count",
    },
}
