# SPDX-FileCopyrightText: 2024-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for moderation tasks."""

from zenodo_rdm.moderation.tasks import _render_breakdown


def test_render_breakdown_groups_drivers_by_rule():
    """Only score-moving reasons are listed, grouped under their rule subtotal."""
    results = {
        "links_rule": {
            "score": 13,
            "reasons": [
                {"score": 5, "label": "7 links in description"},
                {"score": 8, "label": "link to spam domain bad.ru"},
            ],
        },
        # rule that fired nothing is omitted entirely
        "text_sanitization_rule": {
            "score": 0,
            "reasons": [{"score": 0, "label": "2 emoji in metadata"}],
        },
    }
    assert _render_breakdown(results) == (
        "<ul>"
        "<li>links_rule (13)<ul>"
        "<li>+5 7 links in description</li>"
        "<li>+8 link to spam domain bad.ru</li>"
        "</ul></li>"
        "</ul>"
    )


def test_render_breakdown_escapes_labels():
    """Labels embed spammer-controlled text, so they must be HTML-escaped."""
    results = {
        "links_rule": {
            "score": 8,
            "reasons": [{"score": 8, "label": "link to <script>alert(1)</script>"}],
        },
    }
    rendered = _render_breakdown(results)
    assert "<script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered


def test_render_breakdown_empty_when_nothing_fired():
    """A record where no reason moved the score renders no breakdown."""
    results = {
        "links_rule": {"score": 0, "reasons": [{"score": 0, "label": "1 link"}]},
    }
    assert _render_breakdown(results) == ""
