# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""ZenodoRDM exporter tasks."""

from celery import shared_task

from zenodo_rdm.exporter import api


@shared_task
def export_records(formats, community_slug):
    """Export records."""
    return api.export_records(formats, community_slug)
