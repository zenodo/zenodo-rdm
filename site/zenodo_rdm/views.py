"""Additional views."""

from flask import Blueprint

from marshmallow import ValidationError

from .support.support import ZenodoSupport


#
# Registration
#
def create_blueprint(app):
    """Register blueprint routes on app."""

    @app.errorhandler(ValidationError)
    def handle_validation_errors(e):
        if isinstance(e, ValidationError):
            dic = e.messages
            deserialized = []
            for error_tuple in dic.items():
                field, value = error_tuple
                deserialized.append({"field": field, "messages": value})
            return {"errors": deserialized}, 400
        return e.message, 400

    blueprint = Blueprint(
        "zenodo_rdm",
        __name__,
        template_folder="./templates",
    )

    # Support URL rule
    support_endpoint = app.config["SUPPORT_ENDPOINT"] or "/support"
    blueprint.add_url_rule(
        support_endpoint,
        view_func=ZenodoSupport.as_view("support_form"),
    )

    app.register_error_handler(400, handle_validation_errors)

    return blueprint
