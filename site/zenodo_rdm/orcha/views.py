# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Page and banner checks for ai features waitlist."""
from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
)
from flask.views import MethodView
from flask_login import current_user, login_required
from invenio_db import db

# Testing `invenio roles create orcha-waitlist`
WAITLIST_ROLE_NAME = "orcha-waitlist"


def _available_for_user() -> bool:
    """Check if we should be showing this feature to the user."""
    return bool(
        current_app.config.get("RDM_ORCHA_WAITLIST_ENABLED")
        and current_user.is_authenticated
        and current_user.verified_at
    )


def waiting_status():
    """Status for react component."""
    return jsonify(
        show_banner=_available_for_user()
        and not current_user.has_role(WAITLIST_ROLE_NAME)
    )


class OrchaWaitlist(MethodView):
    """Explanation page and opt-in for the waitlist."""

    def dispatch_request(self, **kwargs):
        """Guards both POST and GET requests."""
        if not _available_for_user():
            abort(404)
        return super().dispatch_request(**kwargs)

    def get(self):
        """Renders the template that contains the registration form."""
        return render_template(
            "zenodo_rdm/orcha/waitlist.html",
            already_joined=current_user.has_role(WAITLIST_ROLE_NAME),
        )

    def post(self):
        """Grants the role to the user."""
        datastore = current_app.extensions["security"].datastore
        role = datastore.find_role(WAITLIST_ROLE_NAME)
        if role is None:  # We don't have the role created yet
            abort(503)
        if not current_user.has_role(WAITLIST_ROLE_NAME):
            datastore.add_role_to_user(current_user, role)
            db.session.commit()
        return redirect(request.url)


def create_blueprint(app):
    """Register blueprint."""
    blueprint = Blueprint("zenodo_orcha_waitlist", __name__)
    blueprint.add_url_rule(
        "/ai-assist-features-waitlist",
        view_func=login_required(OrchaWaitlist.as_view("waitlist")),
    )
    blueprint.add_url_rule(
        "/ai-assist-features-waitlist/status", view_func=waiting_status, methods=["GET"]
    )
    return blueprint
