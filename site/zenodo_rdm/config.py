"""Custom code config."""

import os

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

