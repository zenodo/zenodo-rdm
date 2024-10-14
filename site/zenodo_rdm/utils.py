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
from invenio_swh.models import SWHDepositStatus
from invenio_swh.proxies import current_swh_service as service_swh

from zenodo_rdm.openaire.utils import openaire_link


def github_link_render(record):
    """Entry for GitHub."""
    ret = []
    related_identifiers = record.data["metadata"].get("related_identifiers", [])
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
    related_identifiers = record.data["metadata"].get("related_identifiers", [])
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
    related_identifiers = record.data["metadata"].get("related_identifiers", [])
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
    related_identifiers = record.data["metadata"].get("related_identifiers", [])
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
            query.setdefault("name", record.data["metadata"]["title"])
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
    oa_link = openaire_link(record.data)
    if oa_link:
        ret.append(
            dump_external_resource(
                oa_link,
                title="OpenAIRE",
                section=_("Indexed in"),
                icon=url_for("static", filename="images/openaire.svg"),
            )
        )
    return ret


def swh_link_render(record):
    """Render the swh link."""
    permissions = record.has_permissions_to(["manage"])
    can_manage = permissions.get("can_manage", False)

    def _get_success_text(deposit):
        """Get the text to be displayed when the deposit was successful.

        This function takes a `deposit` object as input and returns the text and link
        to be displayed when the deposit was successful. The text is the identifier of
        the deposit, and the link is a URL to the deposit's directory in the SWH UI.

        Examples
        --------
            >>> deposit = Deposit(swhid="swh:1:dir:abc123")
            >>> _get_success_text(deposit)
            ('swh:1:dir:abc123', 'https://swh.example.com/browse/directory/abc123/')

            >>> deposit = Deposit(swhid="swh:1:origin:abc123;origin=https://zenodo.org/record/xyz789")
            >>> _get_success_text(deposit)
            ('swh:1:origin:abc123', 'https://swh.example.com/browse/directory/abc123/')

        """
        swhid = deposit.swhid
        base_url = current_app.config.get("SWH_UI_BASE_URL")
        try:
            swh_link = f"{base_url}/{swhid}"
            swh_text = swhid.split(";")[0]
        except Exception:
            # Handle any exceptions that may occur to avoid breaking the UI
            swh_link = None
            swh_text = None
        return swh_text, swh_link

    def _get_failed_text(deposit):
        """Get the text to be displayed when the deposit failed.

        This is only displayed to users with the "manage" permission.
        """
        if not can_manage:
            return None, None
        return _("Failed to archive."), None

    def _get_waiting_text(deposit):
        """Get the text to be displayed when the deposit is waiting.

        This is only displayed to users with the "manage" permission.
        """
        if not can_manage:
            return None, None
        return _("Waiting to be archived."), None

    if not current_app.config.get("SWH_ENABLED"):
        return None

    ret = []

    d_res = service_swh.get_record_deposit(record._record.id)
    if not d_res.deposit:
        return None
    subtitle = None
    link = None
    if d_res.deposit.status == SWHDepositStatus.FAILED:
        subtitle, link = _get_failed_text(d_res.deposit)

    if d_res.deposit.status == SWHDepositStatus.WAITING:
        subtitle, link = _get_waiting_text(d_res.deposit)

    if d_res.deposit.status == SWHDepositStatus.SUCCESS:
        subtitle, link = _get_success_text(d_res.deposit)

    if not subtitle:
        return None

    ret.append(
        dump_external_resource(
            link or "#",
            title="Software Heritage",
            subtitle=subtitle,
            section=_("Archived in"),
            icon=url_for("static", filename="images/swh.png"),
            template="invenio_swh/swh_link.html",
        )
    )
    return ret


def blr_link_render(record):
    """Entry for BLR."""
    ret = []

    treatmentbank_link = None
    gbif_link = None
    sibils_link = None

    for identifier in record["metadata"]["identifiers"]:
        if re.match(
            "(http|https)://(publication|treatment).plazi.org/id/",
            identifier["identifier"],
            re.I,
        ):
            treatmentbank_link = identifier["identifier"]

    for identifier in record["metadata"]["related_identifiers"]:
        if (
            re.match("(http|https)://www.gbif.org", identifier["identifier"], re.I)
            and identifier["relation_type"]["id"] == "issourceof"
        ):
            gbif_link = identifier["identifier"]
        elif (
            re.match(
                "(http|https)://sibils.text-analytics.ch",
                identifier["identifier"],
                re.I,
            )
            and identifier["relation_type"]["id"] == "issourceof"
        ):
            sibils_link = identifier["identifier"]

    if treatmentbank_link:
        ret.append(
            dump_external_resource(
                treatmentbank_link,
                title="TreatmentBank",
                section=_("Indexed in"),
                icon=url_for("static", filename="images/treatment-bank.png"),
            )
        )

    if gbif_link:
        ret.append(
            dump_external_resource(
                gbif_link,
                title="GBIF",
                section=_("Indexed in"),
                icon=url_for("static", filename="images/gbif.png"),
            )
        )

    if sibils_link:
        ret.append(
            dump_external_resource(
                sibils_link,
                title="SIBiLS",
                section=_("Indexed in"),
                icon=url_for("static", filename="images/sib.png"),
            )
        )
    return ret


def annostor_link_render(record):
    """Entry for annostor."""
    communities = record.data["parent"].get("communities", {}).get("entries", [])
    comm_slugs = {comm["slug"] for comm in communities}

    annostor_communities = current_app.config["ANNOSTOR_COMMUNITIES"]
    as_comm = next(
        (as_comm for as_comm in annostor_communities if as_comm in comm_slugs), None
    )

    if as_comm:
        as_cfg = annostor_communities[as_comm]
        activity = None
        resource_type = record.data["metadata"]["resource_type"]["id"]
        is_annotation_collection = resource_type == "publication-annotationcollection"
        has_iiif_files = any(
            file["ext"] in current_app.config["IIIF_FORMATS"]
            for file in record.data.get("files", {}).get("entries", {}).values()
        )
        if is_annotation_collection:
            activity = "oia:ac"
        elif has_iiif_files:
            activity = "oia:at"

        if activity:
            record_id = record["id"]
            host = as_cfg["annostor_instance"]
            repo = as_cfg["repo_instance"]
            url = f"{host}/annotate/{repo}/{activity}/{record_id}"
            return [
                dump_external_resource(
                    url,
                    title="annostor",
                    section="Open using",
                    subtitle=None,
                    icon=url_for("static", filename="images/annostor.svg"),
                )
            ]

    return []
