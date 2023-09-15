# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Utility functions."""

import re
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import idutils
from flask import current_app, url_for
from invenio_app_rdm.records_ui.utils import dump_external_resource
from invenio_i18n import _


def github_link_render(record):
    """Entry for GitHub."""
    ret = []
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_url = rel_id["scheme"] == "url"
        is_supplement = rel_id["relation_type"]["id"] == "issupplementto"
        url_parts = urlsplit(rel_id["identifier"])
        is_github = url_parts.hostname == "github.com"
        if is_url and is_supplement and is_github:
            release_info = re.match("\/(?P<repo>.+)\/tree\/(?P<tag>.+)", url_parts.path)
            title = "Github"
            subtitle = None
            if release_info:
                title = release_info["repo"]
                subtitle = f"Release: {release_info['tag']}"

            ret.append(
                dump_external_resource(
                    rel_id["identifier"],
                    title=title,
                    section="Available in",
                    subtitle=subtitle,
                    icon=url_for("static", filename="images/github.svg"),
                )
            )
    return ret


def f1000_link_render(record):
    """Entry for F1000."""
    ret = []
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_doi = rel_id["scheme"] == "doi"
        is_cited = rel_id["relation_type"]["id"] == "iscitedby"
        is_f1000_doi = rel_id["identifier"].startswith("10.12688/f1000research")
        if is_doi and is_cited and is_f1000_doi:
            url = idutils.to_url(rel_id["identifier"], rel_id["scheme"], "https")
            ret.append(
                dump_external_resource(
                    url,
                    title="F1000 Research",
                    section=_("Published in"),
                    icon=url_for("static", filename="images/f1000.jpg"),
                )
            )
    return ret


def briefideas_link_render(record):
    """Entry for Brief Ideas."""
    ret = []
    related_identifiers = record.get("ui", {}).get("related_identifiers", [])
    for rel_id in related_identifiers:
        is_url = rel_id["scheme"] == "url"
        is_identical = rel_id["relation_type"]["id"] == "isidenticalto"
        url_parts = urlsplit(rel_id["identifier"])
        is_briefideas = url_parts.hostname == "beta.briefideas.org"
        if is_url and is_identical and is_briefideas:
            ret.append(
                dump_external_resource(
                    rel_id["identifier"],
                    title="Journal of Brief Ideas",
                    section=_("Published in"),
                    icon=url_for("static", filename="images/briefideas.png"),
                )
            )
    return ret


def reana_link_render(record):
    """Entry for REANA."""
    ret = []
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
            ret.append(
                dump_external_resource(
                    urlunsplit(url_parts),
                    title="REANA",
                    section=_("Run in"),
                    icon=url_for("static", filename="images/reana.svg"),
                )
            )
    return ret


def openaire_link_render(record):
    """Entry for OpenAIRE."""
    ret = []
    openaire_types = set(["publication", "dataset", "software", "other"])
    metadata = record.get("metadata", {})
    doi = record.get("pids", {}).get("doi", {}).get("identifier")
    resource_type = metadata.get("resource_type", {}).get("id")
    if resource_type in openaire_types and doi:
        openaire_url = current_app.config.get("OPENAIRE_PORTAL_URL", "")
        url = f"{openaire_url}/search/{resource_type}?pid={doi}"
        ret.append(
            dump_external_resource(
                url,
                title="OpenAIRE",
                section=_("Indexed in"),
                icon=url_for("static", filename="images/openaire.svg"),
            )
        )
    return ret
