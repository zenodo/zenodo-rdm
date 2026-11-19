---
id: jinja-templates
name: Jinja template overrides
paths:
  - "templates/**"
  - "site/zenodo_rdm/templates/**"
---

- Files in `templates/semantic-ui/<upstream_package>/…` **shadow** upstream
  templates with the same path. Changes there should stay minimal. Point out
  copies of upstream templates that will drift, and prefer a `{% block %}`
  extension over copying the whole file when the upstream template allows it.
- Do not mark user or record-controlled data `|safe` without sanitising it.
  Jinja autoescaping is the XSS defence.
- Use `_()` for user-visible text.
- Notification templates (`invenio_notifications/*.jinja`) must define every
  block the notification backend uses (subject, HTML, plain text, Markdown) and
  must handle a missing or deleted record, request or user.
- Email and notification templates must use absolute URLs built from config
  (for example `config.SITE_UI_URL`) or URLs passed in the notification context.
  Never hard-code hostnames such as `zenodo.org`.
