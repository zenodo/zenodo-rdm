# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test legacy serializer grant/funding dumping."""

import pytest
from marshmallow import missing

from zenodo_rdm.legacy.serializers.schemas.zenodojson import MetadataSchema


@pytest.mark.parametrize(
    "funding",
    [
        [{"award": {"number": "101094817", "title": "Some award"}}],  # no funder
        [{"funder": {"id": "00k4n6c32", "name": "EC"}}],  # no award
    ],
)
def test_dump_grants_skips_incomplete_funding(test_app, funding):
    """Funding missing a funder or award is skipped, not crashed (Sentry ZBDZ)."""
    with test_app.app_context():
        assert MetadataSchema().dump_grants({"funding": funding}) is missing


def test_dump_grants_serializes_complete_funding(test_app):
    """Funding with both award and funder produces a legacy grant."""
    funding = [
        {"award": {"number": "755021"}, "funder": {"id": "00k4n6c32", "name": "EC"}}
    ]
    with test_app.app_context():
        grants = MetadataSchema().dump_grants({"funding": funding})
    assert [g["code"] for g in grants] == ["755021"]
