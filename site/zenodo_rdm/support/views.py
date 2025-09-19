# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Implements the support view for ZenodoRDM."""

import mimetypes
from base64 import b64encode
from collections import OrderedDict

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.views import MethodView
from flask_login import current_user
from invenio_accounts.sessions import _extract_info_from_useragent
from invenio_i18n import _
from marshmallow import ValidationError
from requests.exceptions import RequestException
from werkzeug.utils import cached_property
from zammad_py import ZammadAPI

from .schema import SupportFormSchema


class ZenodoSupport(MethodView):
    """Zenodo support view."""

    def __init__(self):
        """Constructor."""
        self.template = "zenodo_rdm/support.html"
        self.support_form_schema = SupportFormSchema()
        self.client = ZammadAPI(
            url=current_app.config["SUPPORT_ZAMMAD_ENDPOINT"],
            http_token=current_app.config["SUPPORT_ZAMMAD_HTTPTOKEN"],
        )

    def get(self):
        """Renders the support template."""
        user_agent = _extract_info_from_useragent(request.headers.get("User-Agent"))
        browser_client = user_agent.get("browser", "") or "Unknown client"
        browser_version = user_agent.get("browser_version", "") or "Unknown version"
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
        try:
            return self.handle_form(data)
        except RequestException:
            # Any error from Zammad being down to badly formatted requests.
            raise Exception(
                "The request could not be sent to the support system due to an internal error."
            )

    def validate_form(self, form_data):
        """Validates form using a schema."""
        return self.support_form_schema.load(form_data)

    def handle_form(self, data):
        """Form controller."""
        customer_id = self.handle_customer(data["email"], data["name"])

        params = {
            "title": data["subject"],
            "group": "Support (1st line)",
            "customer_id": customer_id,
            "sender": "Customer",
            "type": data["category"],
            "article": {
                "subject": data["subject"],
                "body": data["description"],
                "content_type": "text/plain",
                "type": "web",
                "internal": False,
                "sender": "Customer",
                "origin_by_id": customer_id,
            },
        }
        if "files" in data:
            params["article"]["attachments"] = []
            # Limit to max 20 files
            for f in data["files"][:20]:
                params["article"]["attachments"].append(
                    {
                        "filename": f.filename,
                        "data": b64encode(f.stream.read()),
                        "mime-type": mimetypes.guess_type(f.filename)[0]
                        or "application/octet-stream",
                    }
                )

        # Browser info is added as a note.
        if data["sysInfo"]:
            user_agent = _extract_info_from_useragent(request.headers.get("User-Agent"))
            browser_client = user_agent.get("browser", "")
            browser_version = user_agent.get("browser_version", "")
            browser_string = browser_client + " " + browser_version
            platform = user_agent.get("os", "")
            params["article"]["body"] += f"\n\nBrowser: {browser_string} OS: {platform}"

        new_ticket = self.client.ticket.create(params=params)
        return {
            "message": _(
                "You support request #%(ticket_id)s was created. You will receive a confirmation email shortly."
            )
            % {"ticket_id": new_ticket["id"]},
            "type": self.categories[params["type"]]["title"],
            "subject": params["article"]["subject"],
            "body": params["article"]["body"],
        }

    def find_customer(self, email):
        """Find a customer."""
        customer = None
        page = self.client.user.search(f"email:{email}")
        for u in page:
            if u["email"] == email:
                customer = u
                break
        return customer

    def split_name(self, name):
        """Split name into given and family name."""
        parts = name.strip().split(" ")
        if len(parts) == 1:
            return name.strip(), ""
        elif len(parts) > 1:
            return parts[0], " ".join(parts[1:]).strip()
        else:
            return "", ""

    def create_customer(self, email, name, zenodo_user_id):
        """Create a customer."""
        params = {
            "email": email,
            "roles": ["Customer"],
        }
        if name:
            first_name, last_name = self.split_name(name)
            params["firstname"] = first_name
            params["lastname"] = last_name
        if zenodo_user_id is not None:
            params["zenodo_user"] = zenodo_user_id
        return self.client.user.create(params=params)

    def update_customer(self, customer, email, name, zenodo_user_id):
        """Update a customer."""
        params = {}
        if zenodo_user_id:
            if customer.get("zenodo_user", None) != zenodo_user_id:
                params["zenodo_user"] = zenodo_user_id
        if name:
            firstname, lastname = self.split_name(name)
            if customer["firstname"] != firstname:
                params["firstname"] = firstname
            if customer["lastname"] != lastname:
                params["lastname"] = lastname
        if params:
            customer = self.client.user.update(customer["id"], params=params)
        return customer

    def handle_customer(self, email, name):
        """Create the customer in Zammad."""
        # Set initial parameters
        zenodo_user_id = None
        if current_user.is_authenticated:
            email = current_user.email
            name = current_user.user_profile.get("full_name", "")
            zenodo_user_id = current_user.get_id()
        email = email.lower()
        # TODO: Create or update organisation if not already in Zammad.
        customer = self.find_customer(email)
        if customer is None:
            customer = self.create_customer(email, name, zenodo_user_id)
        else:
            self.update_customer(customer, email, name, zenodo_user_id)

        return customer["id"]

    @cached_property
    def categories(self):
        """Return support issue categories."""
        return OrderedDict(
            (c["key"], c) for c in current_app.config["SUPPORT_ISSUE_CATEGORIES"]
        )


def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint("zenodo_support", __name__)

    support_endpoint = app.config.get("SUPPORT_ENDPOINT", "/support")
    blueprint.add_url_rule(
        support_endpoint,
        view_func=ZenodoSupport.as_view("index"),
        strict_slashes=False,
    )

    @blueprint.errorhandler(ValidationError)
    def handle_validation_errors(e):
        """Handle Marshmallow validation errors."""
        messages = e.messages
        deserialized = []
        for error_tuple in messages.items():
            field, value = error_tuple
            deserialized.append({"field": field, "messages": value})
        return {"errors": deserialized}, 400

    return blueprint
