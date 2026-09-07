# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Page and banner checks for ai features waitlist."""

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    request,
)
from flask.views import MethodView
from flask_login import current_user, login_required

# Testing `invenio roles create orcha-waitlist`
WAITLIST_ROLE_NAME = "orcha-waitlist"

# Long-lived browser cookie to stop showing the banner, survives logout
DISMISS_COOKIE = "dismissed_orcha-waitlist-2026"
DISMISS_MAX_AGE = 10 * 365 * 24 * 60 * 60
EU_COMMUNITY_SLUG = "eu"


def _available_for_user() -> bool:
    """Check if we should be showing this feature to the user."""
    return bool(
        current_app.config.get("RDM_ORCHA_WAITLIST_ENABLED")
        and current_user.is_authenticated
        and current_user.verified_at
    )


def _is_eu_project(community_ui) -> bool:
    """Check if the community is an EOR project."""
    parent = (community_ui or {}).get("parent") or {}
    return parent.get("slug") == EU_COMMUNITY_SLUG


def show_orcha_waitlist_banner(community_ui=None, require_community_param=False):
    """Check if the waitlist banner should be shown for the given community.

    :param community_ui: UI serialized community the page is rendered for.
    :param require_community_param: only show the banner if the page was
        reached with a ``?community=<slug>`` querystring parameter.
    """
    if require_community_param and not request.args.get("community"):
        return False
    return bool(
        _available_for_user()
        and not current_user.has_role(WAITLIST_ROLE_NAME)
        and request.cookies.get(DISMISS_COOKIE) != "1"
        and _is_eu_project(community_ui)
    )


def _set_dismiss_cookie(response):
    """Set the cookie that stops the banner from showing."""
    response.set_cookie(
        DISMISS_COOKIE,
        "1",
        max_age=DISMISS_MAX_AGE,
        secure=True,
        httponly=True,
        samesite="Lax",
    )
    return response


def _is_safe_next(next_url) -> bool:
    """Only allow redirecting to relative paths on this site."""
    return bool(next_url) and next_url.startswith("/") and not next_url.startswith("//")


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
            datastore.commit()
        return _set_dismiss_cookie(redirect(request.url))


def dismiss_banner():
    """Stop showing the waitlist banner in this browser."""
    next_url = request.form.get("next")
    if _is_safe_next(next_url):
        response = redirect(next_url)
    else:
        response = current_app.response_class(status=204)
    return _set_dismiss_cookie(response)


def create_blueprint(app):
    """Register blueprint."""
    blueprint = Blueprint("zenodo_orcha_waitlist", __name__)
    blueprint.add_url_rule(
        "/ai-assist-features-waitlist",
        view_func=login_required(OrchaWaitlist.as_view("waitlist")),
    )
    blueprint.add_url_rule(
        "/ai-assist-features-waitlist/dismiss",
        endpoint="dismiss",
        view_func=login_required(dismiss_banner),
        methods=["POST"],
    )

    @blueprint.app_context_processor
    def orcha_waitlist_processor():
        """Make the banner check available to all templates."""
        return {"show_orcha_waitlist_banner": show_orcha_waitlist_banner}

    return blueprint
