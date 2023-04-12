# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Utility functions."""

import re
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from flask import url_for
from invenio_app_rdm.records_ui.utils import dump_external_resource


def github_link_render(record):
    """Entry for GitHub."""
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_url = rel_id["scheme"] == "url"
        is_supplement = rel_id["relation_type"]["id"] == "issupplementedby"
        url_parts = urlsplit(rel_id["identifier"])
        is_github = url_parts.hostname == "github.com"
        release_info = re.match("\/(?P<repo>.+)\/tree\/(?P<tag>.+)", url_parts.path)
        if is_url and is_supplement and is_github and release_info:
            return [
                dump_external_resource(
                    rel_id["identifier"],
                    title=release_info["repo"],
                    section="Available in",
                    subtitle=f"Release: {release_info['tag']}",
                    icon=url_for("static", filename="images/github.svg"),
                )
            ]


def f1000_link_render(record):
    """Entry for F1000."""
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_doi = rel_id["scheme"] == "doi"
        is_cited = rel_id["relation_type"]["id"] == "iscitedby"
        is_f1000_doi = rel_id["identifier"].startswith("10.12688/f1000research")
        if is_doi and is_cited and is_f1000_doi:
            return [
                dump_external_resource(
                    rel_id["identifier"],
                    title="F1000 Research",
                    section="Published in",
                    icon=url_for("static", filename="images/f1000.jpg"),
                )
            ]


def briefideas_link_render(record):
    """Entry for Brief Ideas."""
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_url = rel_id["scheme"] == "url"
        is_identical = rel_id["relation_type"]["id"] == "isidenticalto"
        url_parts = urlsplit(rel_id["identifier"])
        is_briefideas = url_parts.hostname == "beta.briefideas.org"
        if is_url and is_identical and is_briefideas:
            return [
                dump_external_resource(
                    rel_id["identifier"],
                    title="Journal of Brief Ideas",
                    section="Published in",
                )
            ]


def inspire_link_render(record):
    """Entry for INSPIRE."""
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_url = rel_id["scheme"] == "url"
        is_supplement = rel_id["relation_type"]["id"] == "issupplementedby"
        url_parts = urlsplit(rel_id["identifier"])
        is_inspire_url = (
            url_parts.hostname == "inspirehep.net"
            and url_parts.path.startswith("/record/")
        )
        if is_url and is_supplement and is_inspire_url:
            return [
                dump_external_resource(
                    rel_id["identifier"],
                    title="INSPIRE-HEP",
                    section="Available in",
                    icon=url_for("static", filename="images/inspire.svg"),
                )
            ]


def reana_link_render(record):
    """Entry for REANA."""
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        url_parts = urlsplit(rel_id["identifier"])
        is_reana_host = url_parts.hostname in (
            "reana.cern.ch",
            "reana-qa.cern.ch",
            "reana-dev.cern.ch",
        )
        is_reana_launch_path = url_parts.path in ("/launch", "/run")
        if is_reana_host and is_reana_launch_path:
            # Add a "name" if not already there
            query = parse_qs(url_parts.query)
            query.setdefault("name", record["metadata"]["title"])
            url_parts = url_parts._replace(query=urlencode(query))
            return [
                dump_external_resource(
                    urlunsplit(url_parts),
                    title="REANA",
                    section="Run in",
                    icon=url_for("static", filename="images/reana.svg"),
                )
            ]
