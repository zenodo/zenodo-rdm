# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
#
# Zenodo RDM is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.
"""Formatting and displaying checks with diffs."""

import difflib
import itertools

from invenio_i18n import gettext as _
from markupsafe import Markup, escape


def _diff(current, suggested, join_fn):
    """Diff two sequences; join(slice) turns sequence back into escaped HTML."""
    matcher = difflib.SequenceMatcher(None, current, suggested)
    current_parts, suggested_parts = [], []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            chunk = join_fn(current[i1:i2])
            current_parts.append(chunk)
            suggested_parts.append(chunk)
            continue
        if i1 != i2:
            current_parts.append(f'<del class="diff-removed">{join_fn(current[i1:i2])}</del>')
        if j1 != j2:
            suggested_parts.append(f'<ins class="diff-added">{join_fn(suggested[j1:j2])}</ins>')
    return current_parts, suggested_parts

def _diff_words(current_text, suggested_text):
    """Word-level diff of two strings.

    Returns (current_html, suggested_html) with only the words that changed
    wrapped in `<del>`/`<ins>`, so unchanged words render plainly.
    """
    def join_fn(sequence):
        return " ".join(str(escape(w)) for w in sequence)

    current_words = (current_text or "").split()
    suggested_words = (suggested_text or "").split()

    current_parts, suggested_parts = _diff(current_words, suggested_words, join_fn)
    return " ".join(current_parts), " ".join(suggested_parts)


def _diff_chars(current_text, suggested_text):
    """Character-level diff of two strings.

    Same shape as `_diff_words`, but for identifiers like DOIs where a
    single changed character shouldn't highlight the whole value.
    """
    def join_fn(sequence):
        return str(escape(sequence))

    current_text = current_text or ""
    suggested_text = suggested_text or ""

    current_parts, suggested_parts = _diff(current_text, suggested_text, join_fn)
    return "".join(current_parts), "".join(suggested_parts)


def _diff_mapping_item(current, suggested):
    """Diff two comparable dicts key-by-key."""
    current = current or {}
    suggested = suggested or {}

    current_parts = []
    suggested_parts = []
    for key in dict.fromkeys([*current.keys(), *suggested.keys()]):
        c_val = str(current.get(key, ""))
        s_val = str(suggested.get(key, ""))
        if not c_val and not s_val:
            continue
        c_html, s_html = _diff_words(c_val, s_val)
        if c_val:
            current_parts.append(c_html)
        if s_val:
            suggested_parts.append(s_html)

    return ", ".join(current_parts), ", ".join(suggested_parts)


def _diff_funding_item(current, suggested):
    """Diff two funding entries, with 'Award: X (Y), Funder: Z' shape."""
    def build(item, title_html, number_html, funder_html):
        parts = []
        title = item.get("award_title")
        number = item.get("award_number")
        if title and number:
            parts.append(
                _(
                    "Award: %(title)s (%(number)s)",
                    title=Markup(title_html),
                    number=Markup(number_html),
                )
            )
        elif title:
            parts.append(_("Award: %(title)s", title=Markup(title_html)))
        elif number:
            parts.append(_("Award: %(number)s", number=Markup(number_html)))

        if item.get("funder_name") or item.get("funder_id"):
            parts.append(_("Funder: %(funder)s", funder=Markup(funder_html)))

        return ", ".join(str(p) for p in parts)

    current = current or {}
    suggested = suggested or {}

    c_title_html, s_title_html = _diff_words(
        current.get("award_title", ""),
        suggested.get("award_title", ""),
    )
    c_number_html, s_number_html = _diff_chars(
        current.get("award_number", ""), suggested.get("award_number", "")
    )
    c_funder_html, s_funder_html = _diff_words(
        current.get("funder_name") or current.get("funder_id", ""),
        suggested.get("funder_name") or suggested.get("funder_id", ""),
    )

    current_html = build(current, c_title_html, c_number_html, c_funder_html)
    suggested_html = build(suggested, s_title_html, s_number_html, s_funder_html)
    return current_html, suggested_html


def diff_comparison(comparison):
    """Diff-highlight a metadata comparison entry.

    Returns (current_html, suggested_html) Markup, highlighting
    only what changed.
    """
    field = comparison.get("field")
    current = comparison.get("current")
    suggested = comparison.get("suggested")

    if isinstance(current, list) or isinstance(suggested, list):
        diff_fn = _diff_funding_item if field == "funding" else _diff_mapping_item
        current_items = []
        suggested_items = []
        for c_item, s_item in itertools.zip_longest(current or [], suggested or []):
            c_html, s_html = diff_fn(c_item, s_item)
            if c_html:
                current_items.append(f"<li>{c_html}</li>")
            if s_html:
                suggested_items.append(f"<li>{s_html}</li>")
        current_html = (
            f'<ul class="rel-ml-1">{"".join(current_items)}</ul>'
            if current_items
            else "—"
        )
        suggested_html = (
            f'<ul class="rel-ml-1">{"".join(suggested_items)}</ul>'
            if suggested_items
            else "—"
        )
    else:
        diff_fn = _diff_chars if field == "doi" else _diff_words
        current_html, suggested_html = diff_fn(current or "", suggested or "")
        current_html = current_html or "—"
        suggested_html = suggested_html or "—"

    return Markup(current_html), Markup(suggested_html)