from flask import current_app, request
from flask_login import current_user
from flask_mail import Message
from invenio_accounts.sessions import _extract_info_from_useragent

from .utils import format_user_email, render_template_to_string


class EmailService(object):
    """Basic service to send an e-mail using the configured mail extension."""
    @property
    def mail(self):
        service = current_app.extensions["mail"]
        if not service:
            raise Exception("No mail extension provided.")
        return service

    def send_email(
        self, title, recipients, sender, body, reply_to="", attachments=None
    ):
        """Sends an e-mail to the given recipient(s)."""
        if type(recipients) != list:
            recipients = [recipients]

        msg = Message(
            title, sender=sender, recipients=recipients, reply_to=reply_to, body=body
        )
        if attachments:
            for upload in attachments:
                msg.attach(upload.filename, "application/octet-stream", upload.read())
        self.mail.send(msg)


class SupportEmailService(EmailService):
    """_summary_
    Provides an interface to send support related emails.
    """
    def __init__(self):
        """Constructor."""
        super().__init__()

    def send_support_email(
        self, sender_name, email, description, send_user_agent, subject, category, files, title
    ):
        """Sends an email to the configured support."""
        user_agent = _extract_info_from_useragent(request.headers.get("User-Agent"))
        context = {
            "user_id": current_user.get_id(),
            "name": sender_name,
            "email": email,
            "description": description,
            "user_agent": user_agent if send_user_agent else None,
            "subject": subject,
            "category": category,
        }
        msg_body = render_template_to_string(self.support_email_body_template, context)
        msg_title = title
        sender = format_user_email(email, sender_name)
        recipients = self.support_emails
        reply_to = email
        return self.send_email(msg_title, recipients, sender, msg_body, reply_to, files)

    # TODO aggregate in a single method and just pass things
    def send_confirmation_email(self, recipients):
        """Sends a confirmation e-mail to the user."""
        context = {
            "support_name": self.support_sender_name,
            "support_signature": current_app.config["SUPPORT_SIGNATURE"],
        }
        sender = format_user_email(self.support_sender_email, self.support_sender_name)
        msg_body = render_template_to_string(
            self.support_email_confirm_body_template, context
        )
        msg_title = self.support_sender_name
        reply_to = self.support_sender_email
        return self.send_email(msg_title, recipients, sender, msg_body, reply_to)

    @property
    def support_sender_email(self):
        return current_app.config["SUPPORT_SENDER_EMAIL"]

    @property
    def support_sender_name(self):
        return current_app.config["SUPPORT_SENDER_NAME"]

    @property
    def support_email_body_template(self):
        return current_app.config["SUPPORT_EMAIL_BODY_TEMPLATE"]

    @property
    def support_email_confirm_title_template(self):
        return current_app.config["SUPPORT_EMAIL_CONFIRM_TITLE_TEMPLATE"]

    @property
    def support_email_confirm_body_template(self):
        return current_app.config["SUPPORT_EMAIL_CONFIRM_BODY_TEMPLATE"]

    @property
    def support_emails(self):
        return current_app.config["SUPPORT_EMAILS"]
