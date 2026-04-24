# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Theme tasks."""

from celery import shared_task

from .api import featured_communities, recent_uploads


@shared_task(ignore_result=True)
def warm_frontpage_cache():
    """Warm the frontpage data cache."""
    recent_uploads(refresh_cache=True)
    featured_communities(refresh_cache=True)
