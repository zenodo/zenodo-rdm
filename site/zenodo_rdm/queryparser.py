# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Query parsers."""

from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from luqum.tree import Phrase, Word


def word_doi(node):
    """Quote DOIs."""
    if not node.value.startswith("10."):
        return node
    return Phrase(f'"{node.value}"')


def word_communities(node):
    """Resolve community slugs to IDs."""
    slug = node.value
    uuid = (
        db.session.query(CommunityMetadata.id)
        .filter(CommunityMetadata.slug == slug)
        .scalar()
    )
    return Phrase(f'"{uuid}"')


def word_resource_type_subtype(node):
    """Map legacy 'publication-thesis' subtype to 'publication-dissertation'."""
    if node.value == "publication-thesis":
        return Word("publication-dissertation")
    return node


def phrase_resource_type_subtype(node):
    """Map legacy 'publication-thesis' subtype phrase to 'publication-dissertation'."""
    if node.value == '"publication-thesis"':
        return Phrase('"publication-dissertation"')
    return node
