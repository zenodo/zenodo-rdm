# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Custom code config."""

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
    redirect_deposit_new_view,
    redirect_deposit_own_view,
    redirect_formats_to_media_files_view,
    redirect_record_file_preview_view,
    redirect_record_thumbnail_view,
    search_view_function,
)

# Silent warnings
JSONSCHEMAS_HOST = "unused"

# I18N_TRANSLATIONS_PATHS = [os.path.abspath("./site/zenodo_rdm/translations")]

# Email address of sender.
SUPPORT_SENDER_EMAIL = "info@zenodo.org"

# Name of the sender
SUPPORT_SENDER_NAME = "Zenodo Support"

# Support emails
SUPPORT_EMAILS = ["info@zenodo.org"]

# Support signature
SUPPORT_SIGNATURE = "https://zenodo-rdm.web.cern.ch/"

# Support form categories
SUPPORT_ISSUE_CATEGORIES = [
    {
        "key": "file-modification",
        "title": "File modification",
        "description": (
            "All requests related to updating files in already published "
            "record(s). This includes new file addition, file removal or "
            "file replacement. "
            "Before sending a request, please consider creating a "
            '<a href="http://help.zenodo.org/#versioning">new version</a> '
            "of your upload. Please first consult our "
            '<a href="http://help.zenodo.org/#general">FAQ</a> to get familiar'
            " with the file update conditions, to see if your case is "
            "eligible.<br /><br />"
            "You request has to contain <u>all</u> of the points below:"
            "<ol>"
            "<li>Provide a justification for the file change in the "
            "description.</li>"
            "<li>Mention any use of the record(s) DOI in publications or "
            "online, e.g.: list papers that cite your record and "
            "provide links to posts on blogs and social media. "
            "Otherwise, state that to the best of your knowledge the DOI has "
            "not been used anywhere.</li>"
            "<li>Specify the record(s) you want to update <u>by the Zenodo"
            ' URL</u>, e.g.: "https://zenodo.org/record/8428".<br />'
            "<u>Providing only the record's title, publication date or a "
            "screenshot with search result is not explicit enough</u>.</li>"
            "<li>If you want to delete or update a file, specify it "
            "<u>by its filename</u>, and mention if you want the name to "
            "remain as is or changed (by default the filename of the new "
            "file will be used).</li>"
            "<li>Upload the new files below or provide a publicly-accessible "
            "URL(s) with the files in the description.</li>"
            "</ol>"
            "<b><u>Not providing full information on any of the points above "
            "will significantly slow down your request resolution</u></b>, "
            "since our support staff will have to reply back with a request "
            "for missing information."
        ),
    },
    {
        "key": "upload-quota",
        "title": "File upload quota increase",
        "description": (
            "All requests for a quota increase beyond the 50GB limit. "
            "Please include the following information with your request:"
            "<ol>"
            "<li>The total size of your dataset, number of files and the "
            "largest file in the dataset. When referring to file sizes"
            ' use <a href="https://en.wikipedia.org/wiki/IEEE_1541-2002">'
            "SI units</a></li>"
            "<li>Information related to the organization, project or grant "
            "which was involved in the research, which produced the "
            "dataset.</li>"
            "<li>Information on the currently in-review or future papers that "
            "will cite this dataset (if applicable). If possible specify the "
            "journal or conference.</li>"
            "</ol>"
        ),
    },
    {
        "key": "record-inactivation",
        "title": "Record inactivation",
        "description": (
            "Requests related to record inactivation, either by the record "
            "owner or a third party. Please specify the record(s) in question "
            "by the URL(s), and reason for the inactivation."
        ),
    },
    {
        "key": "openaire",
        "title": "OpenAIRE",
        "description": (
            "All questions related to OpenAIRE reporting and grants. "
            "Before sending a request, make sure your problem was not "
            "already resolved, see OpenAIRE "
            '<a href="https://www.openaire.eu/faqs">FAQ</a>. '
            "For questions unrelated to Zenodo, you should contact OpenAIRE "
            '<a href="https://www.openaire.eu/support/helpdesk">'
            "helpdesk</a> directly."
        ),
    },
    {
        "key": "partnership",
        "title": "Partnership, outreach and media",
        "description": (
            "All questions related to possible partnerships, outreach, "
            "invited talks and other official inquiries by media."
            "If you are a journal, organization or conference organizer "
            "interested in using Zenodo as archive for your papers, software "
            "or data, please provide details for your usecase."
        ),
    },
    {
        "key": "tech-support",
        "title": "Security issue, bug or spam report",
        "description": (
            "Report a technical issue or a spam content on Zenodo."
            "Please provide details on how to reproduce the bug. "
            "Upload any screenshots or files which are relevant to the issue "
            "or to means of reproducing it. Include error messages and "
            "error codes you might be getting in the description.<br /> "
            "For REST API errors, provide a minimal code which produces the "
            "issues. Use external services for scripts and long text"
            ', e.g.: <a href="https://gist.github.com/">GitHub Gist</a>. '
            "<strong>Do not disclose your password or REST API access tokens."
            "</strong>"
        ),
    },
    {
        "key": "other",
        "title": "Other",
        "description": ("Questions which do not fit into any other category."),
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

#: Email body template.
SUPPORT_EMAIL_BODY_TEMPLATE = "zenodo_rdm/email_body.html"

#: Email title template.
SUPPORT_EMAIL_TITLE_TEMPLATE = "zenodo_rdm/email_title.html"

#: Email body template.
SUPPORT_EMAIL_CONFIRM_BODY_TEMPLATE = "zenodo_rdm/email_confirm_body.html"

#: Email title template.
SUPPORT_EMAIL_CONFIRM_TITLE_TEMPLATE = "zenodo_rdm/email_confirm_title.html"

# Search query of recent uploads
# Defaults to newest records search
ZENODO_FRONTPAGE_RECENT_UPLOADS_QUERY = "/api/records?sort=newest&size=10"

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
    "geojson": "GeoJSON",
    "xm": "marcxml",
    "dcat": "DCAT-AP",
}

REDIRECTOR_RULES = {
    "redirect_communities_about_legacy": {
        "source": "/communities/about/<id>/",
        "target": communities_detail_view_function,
    },
    "redirect_communities_search_legacy": {
        "source": "/collection/<type>",
        "target": search_view_function,
    },
    "redirect_collections_about": {
        "source": "/collection/user-<id>",
        "target": communities_detail_view_function,
    },
    "redirect_communities_curate": {
        "source": "/communities/<community_id>/curate",
        "target": communities_requests_view_function,
    },
    "redirect_communities_edt": {
        "source": "/communities/<community_id>/edit",
        "target": communities_settings_view_function,
    },
    "redirect_communities_search": {
        "source": "/communities/<community_id>/search",
        "target": communities_records_search,
    },
    "redirect_dev": {
        "source": "/dev",
        "target": "http://developers.zenodo.org",
    },
    "redirect_faq": {
        "source": "/faq",
        "target": "http://help.zenodo.org",
    },
    "redirect_features": {
        "source": "/features",
        "target": "http://help.zenodo.org/features/",
    },
    "redirect_whatsnew": {
        "source": "/whatsnew",
        "target": "http://help.zenodo.org/whatsnew/",
    },
    "redirect_about": {
        "source": "/about",
        "target": "http://about.zenodo.org",
    },
    "redirect_contact": {
        "source": "/contact",
        "target": "http://about.zenodo.org/contact/",
    },
    "redirect_policies": {
        "source": "/policies",
        "target": "http://about.zenodo.org/policies/",
    },
    "redirect_privacy-policy": {
        "source": "/privacy-policy",
        "target": "http://about.zenodo.org/privacy-policy/",
    },
    "redirect_terms": {
        "source": "/terms",
        "target": "http://about.zenodo.org/terms/",
    },
    "redirect_donate": {
        "source": "/donate",
        "target": "https://donate.cernandsocietyfoundation.cern/zenodo/~my-donation?_cv=1",
    },
    "redirect_deposit_id": {
        "source": "/deposit/<pid_value>",
        "target": deposit_view_function,
    },
    "redirect_record_detail": {
        "source": "/record/<pid_value>",
        "target": record_view_function,
    },
    "redirect_record_export": {
        "source": "/record/<pid_value>/export/<export_format>",
        "target": record_export_view,
    },
    "redirect_record_file_download": {
        "source": "/record/<pid_value>/files/<filename>",
        "target": record_file_download_view,
    },
    "redirect_deposit_own": {
        "source": "/deposit",
        "target": redirect_deposit_own_view,
    },
    "redirect_deposit_new": {
        "source": "/deposit/new",
        "target": redirect_deposit_new_view,
    },
    "redirect_record_file_preview": {
        "source": "/record/<pid_value>/preview/<filename>",
        "target": redirect_record_file_preview_view,
    },
    "redirect_record_thumbnail": {
        "source": "/record/<pid_value>/thumb<size>",
        "target": redirect_record_thumbnail_view,
    },
    "redirect_formats_to_media_files": {
        "source": "/record/<pid_value>/formats",
        "target": redirect_formats_to_media_files_view,
    },
}

EXPORT_REDIRECTS = {
    f"redirect_legacy_record_export_view_{key}": {
        "source": f"/records/<pid_value>/export/{key}",
        "target": legacy_record_export_view,
    }
    for key in ZENODO_RECORD_EXPORTERS_LEGACY
}

REDIRECTOR_RULES.update(EXPORT_REDIRECTS)


def lock_edit_record_published_files(record):
    """Custom conditions for file bucket lock."""
    if record:
        is_external_doi = (
            record.get("pids", {}).get("doi", {}).get("provider") == "external"
        )
        if is_external_doi:
            return False
    return True


RDM_LOCK_EDIT_PUBLISHED_FILES = lock_edit_record_published_files
"""Lock editing already published files (enforce record versioning)."""
