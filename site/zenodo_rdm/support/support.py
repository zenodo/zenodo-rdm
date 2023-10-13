# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Implements the support view for ZenodoRDM."""

import smtplib
from collections import OrderedDict

from flask import current_app, redirect, render_template, request, url_for
from flask.views import MethodView
from invenio_accounts.sessions import _extract_info_from_useragent
from werkzeug.utils import cached_property

from .email import SupportEmailService
from .errors import ConfirmationEmailNotSent, SupportEmailNotSent
from .schema import SupportFormSchema


class ZenodoSupport(MethodView):
    """Zenodo support view."""

    def __init__(self):
        """Constructor."""
        self.template = "zenodo_rdm/support.html"
        self.email_service = SupportEmailService()
        self.support_form_schema = SupportFormSchema()

    def get(self):
        """Renders the support template."""
        user_agent = _extract_info_from_useragent(request.headers.get("User-Agent"))
        browser_client = user_agent.get("browser", "")
        browser_version = user_agent.get("browser_version", "")
        browser_string = browser_client + " " + browser_version
        platform = user_agent.get("os", "")
        system_info = {"browser": browser_string, "platform": platform}

        return render_template(
            self.template,
            categories=self.categories,
            system_info=system_info,
        )

    def post(self):
        """Receives a form, validates its data and handles it."""
        input_data = {**request.form.to_dict(), "files": request.files.getlist("files")}
        data = self.validate_form(input_data)
        self.handle_form(data)

        return redirect(url_for("invenio_app_rdm.index"))

    def handle_form(self, form_data):
        """Form controller."""
        self.send_support_email(form_data)
        self.send_confirmation_email(form_data)

    def validate_form(self, form_data):
        """Validates form using a schema."""
        return self.support_form_schema.load(form_data)

    def send_support_email(self, data):
        """Send an email to support."""
        try:
            self.email_service.send_support_email(
                sender_name=data.get("name"),
                email=data.get("email"),
                description=data.get("description"),
                send_user_agent=data.get("sysInfo"),
                subject=data.get("subject"),
                category=data.get("category"),
                files=data.get("files"),
                title="[{}]: {}".format(data.get("category"), data.get("subject")),
            )
        except smtplib.SMTPSenderRefused as e:
            raise SupportEmailNotSent(
                "There was an issue sending an email to the provided "
                "address (ours), please make sure it is correct. "
                "If this issue persists you can send "
                "us an email directly to {}".format(self.email_service.support_emails)
            )
        except Exception as e:
            raise SupportEmailNotSent(
                "There was an issue sending the support request."
                "If this issue persists send us an email directly to {}".format(
                    self.email_service.support_emails
                )
            )

    def send_confirmation_email(self, data):
        """Send a confirmation email to the user."""
        try:
            self.email_service.send_confirmation_email(recipients=data.get("email"))
        except smtplib.SMTPSenderRefused as e:
            raise ConfirmationEmailNotSent(
                "There was an issue sending a confirmation email to the provided "
                "address (yours), please make sure it is correct. "
                "If this issue persists you can send "
                "us an email directly to {}".format(self.email_service.support_emails)
            )
        except Exception as e:
            raise ConfirmationEmailNotSent(
                "There was an issue sending the confirmation email."
                "If this issue persists send us an email directly to {}".format(
                    self.email_service.support_emails
                )
            )

    @cached_property
    def categories(self):
        """Return support issue categories."""
        return OrderedDict(
            (c["key"], c) for c in current_app.config["SUPPORT_ISSUE_CATEGORIES"]
        )

    @cached_property
    def support_emails(self):
        """List of support emails."""
        return current_app.config["SUPPORT_EMAILS"]
