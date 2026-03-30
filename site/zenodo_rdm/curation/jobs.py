# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Jobs module."""

from datetime import datetime, timezone

from invenio_i18n import lazy_gettext as _
from invenio_jobs.jobs import JobType

from zenodo_rdm.curation.tasks import run_eu_record_curation


class EURecordCuration(JobType):
    """EU Record Curation Job."""

    task = run_eu_record_curation
    description = _("Curate published records for EU community")
    title = _("EU Record Curation")
    id = "eu_record_curation"

    @classmethod
    def build_task_arguments(cls, job_obj, since=None, **kwargs):
        """We only need the since argument."""
        return {"since": since or datetime.now(timezone.utc)}
