# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Metadata comparison check using orcha."""

import hashlib
import html
import json
from dataclasses import dataclass, field

import bleach
import requests
from invenio_checks.base import Check, CheckResult
from invenio_checks.models import CheckConfig

from zenodo_rdm.orcha.utils import run_compare_metadata_workflow


@dataclass
class ComparisonCheckResult(CheckResult):
    """CheckResult with additional fields for comparison checks."""
    describes_file: bool = False
    comparisons: list[dict] = field(default_factory=list)


class MetadataComparisonCheck(Check):
    """Check whether a record's metadata accurately describes its uploaded file."""

    id = "compare_metadata"
    title = "Metadata comparison check"
    description = (
        "Compares the record's metadata against the content of the uploaded file."
    )
    sort_order = 35
    sync = False
    target_type = "record"

    default_messages = {
        "title": "Record's metadata should match content of the uploaded file.",
        "description": "The system compares the record metadata against the uploaded file.",
    }

    def _get_file_checksum(self, record):
        """Return the checksum of the single uploaded file, or None."""
        files = record.files
        if not files or not files.entries:
            return None
        file_keys = list(files.entries.keys())
        if len(file_keys) != 1:
            return None
        ov = record.files[file_keys[0]].object_version
        if not ov:
            return None
        return ov.file.checksum if ov.file else None

    def _get_input_hash(self, record):
        """Return a hash of the inputs used to detect when the check needs to rerun."""
        input_data = {
            **self._extract_metadata(record),
            "file_checksum": self._get_file_checksum(record),
        }
        return hashlib.sha256(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()

    def should_rerun(self, record, config, previous_run, **kwargs):
        """Return True if metadata fields or the uploaded file changed since the last run."""
        return previous_run.state.get("input_hash") != self._get_input_hash(record)

    def _strip_html(self, value):
        """Convert rich-text HTML (e.g. a description) to plain text."""
        text = bleach.clean(value, tags=[], attributes=[], strip=True)
        return " ".join(html.unescape(text).split())

    def _extract_metadata(self, record):
        """Extract a flat metadata dict from the record for the comparison workflow."""
        metadata = record.get("metadata", {})
        pids = record.get("pids", {})

        creators = []
        for c in metadata.get("creators", []):
            p = c.get("person_or_org", {})
            family = p.get("family_name", "")
            given = p.get("given_name", "")
            name = f"{family}, {given}".strip(", ") if given else family
            orcid = next(
                (
                    i["identifier"]
                    for i in p.get("identifiers", [])
                    if i.get("scheme") == "orcid"
                ),
                None,
            )
            affiliations = c.get("affiliations") or []
            affiliation = affiliations[0].get("name") if affiliations else None
            creators.append({"name": name, "orcid": orcid, "affiliation": affiliation})

        licenses = []
        for right in metadata.get("rights", []):
            entry = {"id": right.get("id", "")}
            if right_title := right.get("title"):
                entry["title"] = right_title.get("en", "")
            licenses.append(entry)

        return {
            "title": metadata.get("title", ""),
            "description": self._strip_html(metadata.get("description", "")),
            "creators": creators,
            "publication_date": metadata.get("publication_date", ""),
            "doi": pids.get("doi", {}).get("identifier", ""),
            "license": licenses,
            "copyright": metadata.get("copyright", ""),
            "funding": metadata.get("funding", []),
        }

    def run(self, record, config: CheckConfig, **kwargs):
        """Run the metadata comparison check."""

        def get_updated_result(check_result, message, success):
            check_result.success = success
            check_result.description = message
            if not success:
                check_result.errors.append(
                    {
                        "messages": [message],
                        "description": description,
                        "severity": config.severity.error_value,
                    }
                )
            return check_result

        params = config.params
        description = params.get(
            "compare_metadata_description",
            self.default_messages["description"],
        )
        check_result = ComparisonCheckResult(
            id=self.id,
            title=params.get("compare_metadata_title", self.default_messages["title"]),
            description=description,
        )

        files = record.files
        if not files or not files.entries:
            check_result.success = False
            check_result.description = "Record has no files to compare against."
            return check_result, {}

        file_keys = list(files.entries.keys())
        if len(file_keys) > 1:
            msg = "Metadata check only supports records with a single file."
            return get_updated_result(check_result, msg, False), {}

        file_key = file_keys[0]
        if not (files.mimetypes[0] == "application/pdf" and file_key.endswith(".pdf")):
            msg = "Metadata check only supports PDF files."
            return get_updated_result(check_result, msg, False), {}

        pid_value = record.pid.pid_value
        current_metadata = self._extract_metadata(record)

        try:
            status, result = run_compare_metadata_workflow(
                pid_value, file_key, current_metadata
            )
        except (RuntimeError, requests.ConnectionError, requests.HTTPError):
            msg = "Metadata comparison service unavailable."
            return get_updated_result(check_result, msg, False), {}
        except requests.Timeout:
            msg = "Metadata comparison service timed out, please try again."
            return get_updated_result(check_result, msg, False), {}

        if status == "error":
            msg = "Error running the metadata comparison check. Please try again later."
            return get_updated_result(check_result, msg, False), {}
        if status == "timeout":
            msg = "Metadata comparison service timed out, please try again."
            return get_updated_result(check_result, msg, False), {}

        describes_file = result.get("describes_file")
        decision = result.get("decision", "")
        comparisons = result.get("comparisons", [])

        check_result.success = bool(describes_file)
        check_result.description = decision

        if not describes_file:
            check_result.add_errors(
                [
                    {
                        "field": "metadata",
                        "messages": [decision],
                        "description": decision,
                        "severity": config.severity.error_value,
                    }
                ]
            )

        check_result.describes_file = describes_file
        check_result.comparisons = comparisons
        return check_result, {
            "workflow_id": result.get("workflow_id"),
            "input_hash": self._get_input_hash(record),
        }
