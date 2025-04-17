# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter jobs."""

from invenio_i18n import lazy_gettext as _
from invenio_jobs.jobs import JobType

from zenodo_rdm.exporter.tasks import export_community_records


class ExportCommunityRecords(JobType):
    """Export Community Records Job."""

    task = export_community_records
    description = _("Export records of a given community in a given format")
    title = _("Export Community Records")
    id = "export_community_records"

    @classmethod
    def build_task_arguments(cls, job_obj, since=None, **kwargs):
        """Generate default job arguments."""
        # TODO: Use `example-community-slug` when custom args work properly.
        return {"community_slug": "biosyslit"}
