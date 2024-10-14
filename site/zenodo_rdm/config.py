# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Custom code config."""

from .params import ZenodoArgsSchema, ZenodoSearchOptions
from .redirector import (
    communities_detail_view_function,
    communities_records_search,
    communities_requests_view_function,
    communities_settings_view_function,
    deposit_view_function,
    legacy_record_export_view,
    record_export_view,
    record_file_download_view,
    record_view_function,
    redirect_access_request,
    redirect_deposit_new_view,
    redirect_deposit_own_view,
    redirect_formats_to_media_files_view,
    redirect_licenses,
    redirect_record_file_preview_view,
    redirect_record_thumbnail_view,
    redirect_records_search_slash,
    search_view_function,
)

# I18N_TRANSLATIONS_PATHS = [os.path.abspath("./site/zenodo_rdm/translations")]

# API endpoint to Zammad instance
SUPPORT_ZAMMAD_ENDPOINT = "http://localhost:8080/api/v1"

# Zammad token
SUPPORT_ZAMMAD_HTTPTOKEN = "changeme"

# Support form categories
SUPPORT_ISSUE_CATEGORIES = [
    {
        "key": "general-inquiry",
        "title": "General inquiry",
        "description": "",
    },
    {
        "key": "problem-report",
        "title": "Bug or problem",
        "description": "Please provide direct links to pages and screenshots if possible. Include the <strong>error identifier</strong> if shown.",
    },
    {
        "key": "file-modification",
        "title": "File modification",
        "description": (
            "File modifications are possible within a short grace period after publishing:"
            "<ul>"
            "<li><strong>Published <=30 days (accepted):</strong> File modifications are accepted within a 30 days grace period after publishing your record.</li>"
            '<li><strong>Published >30 days (declined):</strong> Please use our <a href="https://help.zenodo.org/docs/deposit/manage-versions/">versioning feature</a> for records published >30 days ago. File modification requests made after the 30-day grace period are declined.</li>'
            "</ul>"
            "Please provide the following information:"
            "<ul>"
            "<li><strong>Justification:</strong> Short justification for the file change.</li>"
            "<li><strong>Record URL:</strong> Please provide a direct link to the record you would like to modify (e.g. https://zenodo.org/records/1234).</li>"
            "<li><strong>Actions:</strong> Please specify all changes you would like to perform (add/replace/delete/rename). Please specify the exact <strong>filename</strong> for each action.</li>"
            "<li><strong>Files:</strong> Please provide the files on a publicly-accessible URL(s) or for smaller files attach them on the form.</li>"
            "</ul>"
        ),
    },
    {
        "key": "quota-increase",
        "title": "Quota increase",
        "description": (
            "<p>We exceptionally grant a <strong>one-time quota increase up to 200GB</strong>. Requests beyond the 200GB are declined. Zenodo allows maximum 100 files in a record (this limit cannot be increased).</p>"
            '<p><strong>Before you send the request</strong>, please follow the actions described on <a href="https://help.zenodo.org/docs/deposit/manage-files/quota-increase/">https://help.zenodo.org/docs/deposit/manage-files/quota-increase/</a>.</p>'
        ),
    },
    {
        "key": "record-deletion",
        "title": "Record deletion",
        "description": (
            "<p>The request must be made by the uploader (if you're not the uploader, choose <em>take-down notice</em> instead).</p>"
            "<p>Record deletion is possible within a short grace period after publishing:</p>"
            "<ul>"
            "<li><strong>Published <=30 days (accepted):</strong> Record deletions are accepted within a 30 days grace period after publishing your record.</li>"
            '<li><strong>Published >30 days (declined):</strong> Please use our <a href="https://help.zenodo.org/docs/deposit/manage-versions/">versioning feature</a> for records published >30 days ago. File modification requests made after the 30-day grace period are declined.</li>'
            "</ul>"
            "<p>Please provide:</p>"
            "<ul>"
            "<li><strong>Record URL:</strong> A direct link to the record you would like to delete (e.g. https://zenodo.org/records/1234). If multiple versions should be deleted, please include one link per version.</li>"
            "</ul>"
        ),
    },
    {
        "key": "user-deletion",
        "title": "User deletion",
        "description": (
            "Please make sure you <strong>log in before you send the request</strong>. If you have uploaded any records or created any communities, please specify to who these should be transferred."
        ),
    },
    {
        "key": "ownership-transfer",
        "title": "Ownership transfer",
        "description": "",
    },
    {
        "key": "personal-data-report",
        "title": "Report personal data exposure",
        "description": (
            "<p>Please provide the following information:</p>"
            "<ul>"
            "<li><strong>Link:</strong> A direct link to the record containing personal data.</li>"
            "<li><strong>Reason:</strong> A description of where the personal data appears.</li>"
            "</ul>"
        ),
    },
    {
        "key": "security-report",
        "title": "Report a security issue",
        "description": "Please provide as detailed information as possible.",
    },
    {
        "key": "spam-report",
        "title": "Report spam",
        "description": (
            "<p>Please provide the following information:</p>"
            "<ul>"
            "<li><strong>Link:</strong> A direct link to the spam record/community.</li>"
            "<li><strong>Reason:</strong> A short description of why the record is spam.</li>"
            "</ul>"
        ),
    },
    {
        "key": "feature-request",
        "title": "Feedback/Feature request",
        "description": "",
    },
    {
        "key": "take-down",
        "title": "Take-down notice",
        "description": (
            "Please provide a direct link to the record or community to request us to take down. Please specify the reason for the take-down (e.g. copyright infringement, plagiarism, fraud, or similar)."
        ),
    },
]

#: Maximum size of attachment in contact form.
SUPPORT_ATTACHMENT_MAX_SIZE = 1000 * 1000 * 10  # 10 MB

#: Description maximum length.
SUPPORT_DESCRIPTION_MAX_LENGTH = 5000

#: Description minimum length.
SUPPORT_DESCRIPTION_MIN_LENGTH = 20

# Support url endpoint
SUPPORT_ENDPOINT = "/support"

# Search query of recent uploads
# Defaults to newest records search
ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY = "type:(dataset OR software OR poster OR presentation) AND _exists_:parent.communities AND access.files:public"

# Citations
# =========
ZENODO_RECORDS_UI_CITATIONS_ENDPOINT = (
    "https://zenodo-broker-qa.web.cern.ch/api/relationships"
)

# Redirection
# ===========

ZENODO_RECORD_EXPORTERS_LEGACY = {
    "hx": "bibtex",
    "dcite4": "datacite-xml",
    "xd": "dublincore",
    "xm": "marcxml",
    "dcat": "DCAT-AP",
}

REDIRECTOR_RULES = {
    "redirect_communities_about_legacy": {
        "source": "/communities/about/<id>",
        "rule_options": {"strict_slashes": False},
        "target": communities_detail_view_function,
    },
    "redirect_communities_search_legacy": {
        "source": "/collection/<type>",
        "rule_options": {"strict_slashes": False},
        "target": search_view_function,
    },
    "redirect_collections_about": {
        "source": "/collection/user-<id>",
        "rule_options": {"strict_slashes": False},
        "target": communities_detail_view_function,
    },
    "redirect_communities_curate": {
        "source": "/communities/<community_id>/curate",
        "rule_options": {"strict_slashes": False},
        "target": communities_requests_view_function,
    },
    "redirect_communities_edt": {
        "source": "/communities/<community_id>/edit",
        "rule_options": {"strict_slashes": False},
        "target": communities_settings_view_function,
    },
    "redirect_communities_search": {
        "source": "/communities/<community_id>/search",
        "rule_options": {"strict_slashes": False},
        "target": communities_records_search,
    },
    "redirect_dev": {
        "source": "/dev",
        "rule_options": {"strict_slashes": False},
        "target": "http://developers.zenodo.org",
    },
    "redirect_faq": {
        "source": "/faq",
        "rule_options": {"strict_slashes": False},
        "target": "http://help.zenodo.org",
    },
    "redirect_features": {
        "source": "/features",
        "rule_options": {"strict_slashes": False},
        "target": "http://help.zenodo.org/features/",
    },
    "redirect_whatsnew": {
        "source": "/whatsnew",
        "rule_options": {"strict_slashes": False},
        "target": "http://help.zenodo.org/whatsnew/",
    },
    "redirect_about": {
        "source": "/about",
        "rule_options": {"strict_slashes": False},
        "target": "http://about.zenodo.org",
    },
    "redirect_contact": {
        "source": "/contact",
        "rule_options": {"strict_slashes": False},
        "target": "http://about.zenodo.org/contact/",
    },
    "redirect_policies": {
        "source": "/policies",
        "rule_options": {"strict_slashes": False},
        "target": "http://about.zenodo.org/policies/",
    },
    "redirect_privacy-policy": {
        "source": "/privacy-policy",
        "rule_options": {"strict_slashes": False},
        "target": "http://about.zenodo.org/privacy-policy/",
    },
    "redirect_terms": {
        "source": "/terms",
        "rule_options": {"strict_slashes": False},
        "target": "http://about.zenodo.org/terms/",
    },
    "redirect_donate": {
        "source": "/donate",
        "rule_options": {"strict_slashes": False},
        "target": "https://donate.cernandsocietyfoundation.cern/zenodo/~my-donation?_cv=1",
    },
    "redirect_deposit_id": {
        "source": "/deposit/<pid_value>",
        "rule_options": {"strict_slashes": False},
        "target": deposit_view_function,
    },
    "redirect_record_detail": {
        "source": "/record/<pid_value>",
        "rule_options": {"strict_slashes": False},
        "target": record_view_function,
    },
    "redirect_record_export": {
        "source": "/record/<pid_value>/export/<export_format>",
        "rule_options": {"strict_slashes": False},
        "target": record_export_view,
    },
    "redirect_record_file_download": {
        "source": "/record/<pid_value>/files/<path:filename>",
        "rule_options": {"strict_slashes": False},
        "target": record_file_download_view,
    },
    "redirect_deposit_own": {
        "source": "/deposit",
        "rule_options": {"strict_slashes": False},
        "target": redirect_deposit_own_view,
    },
    "redirect_deposit_new": {
        "source": "/deposit/new",
        "rule_options": {"strict_slashes": False},
        "target": redirect_deposit_new_view,
    },
    "redirect_record_file_preview": {
        "source": "/record/<pid_value>/preview/<path:filename>",
        "rule_options": {"strict_slashes": False},
        "target": redirect_record_file_preview_view,
    },
    "redirect_record_thumbnail": {
        "source": "/record/<pid_value>/thumb<size>",
        "rule_options": {"strict_slashes": False},
        "target": redirect_record_thumbnail_view,
    },
    "redirect_formats_to_media_files": {
        "source": "/record/<pid_value>/formats",
        "rule_options": {"strict_slashes": False},
        "target": redirect_formats_to_media_files_view,
    },
    "redirect_access_request": {
        "source": "/account/settings/sharedlinks/accessrequest/<number>",
        "rule_options": {"strict_slashes": False},
        "target": redirect_access_request,
    },
}


API_REDIRECTOR_RULES = {
    "redirect_records_search_slash": {
        "source": "/records/",
        "target": redirect_records_search_slash,
    },
    "redirect_licenses": {
        "source": "/licenses",
        "rule_options": {"strict_slashes": False},
        "target": redirect_licenses,
    },
}

EXPORT_REDIRECTS = {
    f"redirect_legacy_record_export_view_{key}": {
        "source": f"/records/<pid_value>/export/{key}",
        "rule_options": {"strict_slashes": False},
        "target": legacy_record_export_view,
    }
    for key in ZENODO_RECORD_EXPORTERS_LEGACY
}

REDIRECTOR_RULES.update(EXPORT_REDIRECTS)


def lock_edit_record_published_files(service, identity, record=None, draft=None):
    """Custom conditions for file bucket lock."""
    can_modify = service.check_permission(
        identity, "modify_locked_files", record=record
    )
    if can_modify:
        return False

    return True


RDM_LOCK_EDIT_PUBLISHED_FILES = lock_edit_record_published_files
"""Lock editing already published files (enforce record versioning)."""

APP_RDM_RECORD_THUMBNAIL_SIZES = [
    10,
    50,
    100,
    250,
    750,
    1200,
]
"""Thumbnail sizes."""


RDM_SEARCH_OPTIONS_CLS = ZenodoSearchOptions
"""Zenodo search options class to support legacy search parameters."""


RDM_SEARCH_ARGS_SCHEMA = ZenodoArgsSchema
"""Zenodo search args schema to support legacy search parameters."""

THEME_MATHJAX_CDN = (
    "//cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js"
    "?config=TeX-AMS-MML_HTMLorMML"
)
