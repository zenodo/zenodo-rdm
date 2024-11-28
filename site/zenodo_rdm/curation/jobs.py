# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Jobs module."""

from datetime import datetime, timezone

from invenio_i18n import lazy_gettext as _
from invenio_jobs.jobs import JobType
from marshmallow import Schema, fields
from marshmallow_utils.fields import ISODateString

from zenodo_rdm.curation.tasks import run_eu_record_curation


class ArgsSchema(Schema):
    """Schema of task input arguments."""

    since = ISODateString()
    job_arg_schema = fields.String(
        metadata={"type": "hidden"},
        dump_default="ArgsSchema",
        load_default="ArgsSchema",
    )


class EURecordCuration(JobType):
    """EU Record Curation Job."""

    arguments_schema = ArgsSchema
    task = run_eu_record_curation
    description = _("Curate published records for EU community")
    title = _("EU Record Curation")
    id = "eu_record_curation"

    @classmethod
    def default_args(cls, job_obj, since=None, **kwargs):
        """Generate default job arguments here."""
        if since is None and job_obj.last_runs["success"]:
            since = job_obj.last_runs["success"].started_at
        else:
            since = since or datetime.now(timezone.utc)

        return {"since": str(since)}
