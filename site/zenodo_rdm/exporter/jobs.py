# SPDX-FileCopyrightText: 2025 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
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
        use_pit = current_app.config.get("EXPORTER_JOB_USE_PIT", False)
        page_size = current_app.config.get("EXPORTER_JOB_PAGE_SIZE", 1000)
        return {
            "format": default_format,
            "community_slug": default_community_slug,
            "use_pit": use_pit,
            "page_size": page_size,
        }
