# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Statistics events builders."""

from zenodo.modules.records.utils import is_deposit

from .utils import extract_event_record_metadata, get_record_from_context


def skip_deposit(event, sender_app, **kwargs):
    """Check if event is coming from deposit record and skip."""
    record = get_record_from_context(**kwargs)
    if record and is_deposit(record):
        # TODO: Check that invenio-stats bails when `None` is returned
        return None
    return event


def add_record_metadata(event, sender_app, **kwargs):
    """Add Zenodo-specific record fields to the event."""
    record = get_record_from_context(**kwargs)
    if record:
        event.update(extract_event_record_metadata(record))
    return event
