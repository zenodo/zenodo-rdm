# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Form for user profiles."""

from invenio_i18n import lazy_gettext as _
from invenio_userprofiles.forms import ProfileForm, strip_filter
from wtforms import StringField, validators
from wtforms.validators import DataRequired, EqualTo, Length


class ZenodoProfileForm(ProfileForm):
    """Form for editing user profile with stricter validation."""

    full_name = StringField(
        _("Full name"),
        validators=[
            Length(max=255),
            DataRequired(message=_("Full name not provided.")),
        ],
        filters=[strip_filter],
    )

    affiliations = StringField(
        _("Affiliations"),
        validators=[
            Length(max=255),
            DataRequired(message=_("Affiliations not provided.")),
        ],
        filters=[strip_filter],
    )
