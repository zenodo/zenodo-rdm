# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

import pytest

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates" / "security" / "email"

@pytest.mark.parametrize(
    "template_path",
    sorted(TEMPLATES_DIR.glob("*.html")),
    ids=lambda p: p.name,
)
def test_no_full_name_reference(template_path):
    """Make sure we dont introduce `full_name` into any email we send"""
    assert "full_name" not in template_path.read_text()
