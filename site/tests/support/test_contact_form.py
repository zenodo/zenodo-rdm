# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test support contact form."""

import pytest
from marshmallow import ValidationError

from zenodo_rdm.support.support import ZenodoSupport


@pytest.fixture
def support_view():
    return ZenodoSupport()


@pytest.fixture
def support_email_service(support_view):
    return support_view.email_service


@pytest.fixture
def form_json_data():
    return {
        "name": "John Doe",
        "email": "john_doe@invenio.org",
        "category": "file-modification",
        "description": "Hi! I need some help with my record ...",
        "subject": "Record file is wrong",
        "sysInfo": False,
        "files": [],
    }


def test_form_validation_valid(form_json_data, support_view, test_app):
    """Tests form with valid data."""
    validated_data = support_view.validate_form(form_json_data)
    assert validated_data
    assert type(validated_data) == dict
    assert validated_data == form_json_data


def test_form_validation_invalid_unknown_fields(form_json_data, support_view):
    """Tests invalid form with unknown fields."""
    invalid_data = {**form_json_data, "unknown": "Unknown field"}
    with pytest.raises(ValidationError):
        support_view.validate_form(invalid_data)


def test_form_validation_invalid_description(form_json_data, support_view, test_app):
    """Tests form with invalid description."""
    min_length = test_app.config["SUPPORT_DESCRIPTION_MIN_LENGTH"]
    # Small description should fail
    invalid_data = {**form_json_data, "description": "a" * (min_length - 1)}
    with pytest.raises(ValidationError):
        support_view.validate_form(invalid_data)

    max_length = test_app.config["SUPPORT_DESCRIPTION_MAX_LENGTH"]
    # Large description should fail
    invalid_data = {**form_json_data, "description": "a" * (max_length + 1)}
    with pytest.raises(ValidationError):
        support_view.validate_form(invalid_data)


def test_form_validation_invalid_categories(form_json_data, support_view):
    """Tests form with invalid category."""
    # Invalid category should fail
    invalid_data = {**form_json_data, "category": "invalid-category"}
    with pytest.raises(ValidationError):
        support_view.validate_form(invalid_data)


def test_form_validation_invalid_required_fields(form_json_data, support_view):
    """Tests form with missing required field."""
    invalid_data = {**form_json_data, "name": None}
    with pytest.raises(ValidationError):
        support_view.validate_form(invalid_data)
