"""Additional views."""

from flask import Blueprint, render_template


def support():
    return render_template("zenodo_rdm/support.html")


#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""
    blueprint = Blueprint(
        "zenodo_rdm",
        __name__,
        template_folder="./templates",
    )

    # Record URL rules
    blueprint.add_url_rule(
        "/support",
        view_func=support,
    )

    return blueprint
