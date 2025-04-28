# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""ZenodoRDM exporter jobs."""

from flask import current_app
from invenio_i18n import lazy_gettext as _
from invenio_jobs.jobs import JobType

from zenodo_rdm.exporter.tasks import export_records


class ExportRecords(JobType):
    """Export Records Job."""

    task = export_records
    description = _("Export records in a given format for given (optional) community ")
    title = _("Export Records")
    id = "export_records"

    @classmethod
    def build_task_arguments(cls, job_obj, since=None, **kwargs):
        """Generate default job arguments."""
        default_format = current_app.config["EXPORTER_JOB_DEFAULT_FORMAT"]
        default_community_slug = current_app.config[
            "EXPORTER_JOB_DEFAULT_COMMUNITY_SLUG"
        ]
        return {"format": default_format, "community_slug": default_community_slug}
