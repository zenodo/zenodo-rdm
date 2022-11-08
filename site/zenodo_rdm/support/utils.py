from flask import current_app


def render_template_to_string(template, context):
    """Render a Jinja template with the given context."""
    template = current_app.jinja_env.get_or_select_template(template)
    return template.render(context)


def format_user_email(email, name):
    """Format the user's email as 'Full Name <email>' or 'email'."""
    if name:
        email = "{name} <{email}>".format(name=name, email=email)
    return email
