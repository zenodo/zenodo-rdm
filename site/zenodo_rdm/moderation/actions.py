# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""RDM user moderation action."""

from flask import current_app
from flask_mail import Message
from invenio_app_rdm.utils.files import render_email_from_context
from invenio_users_resources.records.api import UserAggregate

_BLOCK_NOTIFICATION_HTML = "zenodo_rdm/moderation/block_notification.html"
_BLOCK_NOTIFICATION_TXT = "zenodo_rdm/moderation/block_notification.txt"


def on_block_notify(user_id, uow=None, actor_id=None, **kwargs):
    """Send a notification email to a user blocked by the automated system."""
    if actor_id is not None:
        return

    user = UserAggregate.get_record(user_id)

    context = {
        "full_name": (user.profile or {}).get("full_name", ""),
        "user_id": user_id,
    }

    mail_ext = current_app.extensions["mail"]
    msg = Message(
        subject="Notice of account suspension on Zenodo",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user.email],
        reply_to=current_app.config["MAIL_DEFAULT_SUPPORT"],
        body=render_email_from_context(_BLOCK_NOTIFICATION_TXT, context),
        html=render_email_from_context(_BLOCK_NOTIFICATION_HTML, context),
    )
    try:
        mail_ext.send(msg)
    except Exception:
        current_app.logger.exception(
            "Failed to send block notification email.",
            extra={"user_id": user_id}
        )
