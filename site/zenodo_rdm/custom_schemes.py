# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Custom scheme config."""

import re

# Regular expression to validate EDMO identifiers in the format "edmo:<ID>"
edmo_regexp = re.compile(r"^edmo:(\d+)$")

# Regular expression to match the EDMO URL format
edmo_url_regexp = re.compile(
    r"(?:https?://)?(?:edmo\.seadatanet\.org/report/)?(\d+)$", re.IGNORECASE
)


def is_edmo(val):
    """
    Validate and normalize an EDMO identifier or URL.

    Returns the normalized 'edmo:<ID>' format if valid, otherwise None.
    """
    # Match against the URL or the edmo:<ID> format
    match = edmo_url_regexp.match(val) or edmo_regexp.match(val)
    if match:
        # Extract the numeric ID from the matched group
        return f"edmo:{match.group(1)}"
    return None


def normalize_edmo(val):
    """Normalize an EDMO identifier or URL to the 'edmo:<ID>' format."""
    return is_edmo(val)


def generate_edmo_url(_, normalized_pid):
    """
    Generate a URL for a given normalized EDMO identifier.

    Assumes the input is in the form 'edmo:<ID>'.
    """
    edmo_id = normalized_pid.split(":")[1]
    return f"https://edmo.seadatanet.org/report/{edmo_id}"


def get_scheme_config_func():
    """Return the configuration for the EDMO custom scheme."""
    return {
        "validator": is_edmo,
        "normalizer": normalize_edmo,
        "filter": [],
        "url_generator": generate_edmo_url,
    }
