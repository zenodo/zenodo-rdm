# SPDX-FileCopyrightText: 2024 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Query parsers."""

from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_records_resources.services.records.queryparser import FieldValueMapper
from luqum.tree import Phrase, Word


def word_doi(node):
    """Quote DOIs."""
    if not node.value.startswith("10."):
        return node
    return Phrase(f'"{node.value}"')


def _resolve_community_slug(slug):
    return (
        db.session.query(CommunityMetadata.id)
        .filter(CommunityMetadata.slug == slug)
        .scalar()
    )


def word_communities(node):
    """Resolve community slugs to IDs."""
    return Phrase(f'"{_resolve_community_slug(node.value)}"')


def phrase_communities(node):
    """Resolve quoted community slugs to IDs."""
    # node.value includes the surrounding double quotes.
    return Phrase(f'"{_resolve_community_slug(node.value.strip(chr(34)))}"')


def word_thesis_to_dissertation(node):
    """Map legacy 'publication-thesis' value to 'publication-dissertation'."""
    if node.value == "publication-thesis":
        return Word("publication-dissertation")
    return node


def phrase_thesis_to_dissertation(node):
    """Map legacy 'publication-thesis' phrase to 'publication-dissertation'."""
    if node.value == '"publication-thesis"':
        return Phrase('"publication-dissertation"')
    return node


def _thesis_value_mapper(term_name):
    """Rewrite 'publication-thesis' to 'publication-dissertation'."""
    return FieldValueMapper(
        term_name,
        word=word_thesis_to_dissertation,
        phrase=phrase_thesis_to_dissertation,
    )


ZENODO_LEGACY_SEARCH_MAP = {
    "resource_type.subtype": _thesis_value_mapper(
        "metadata.resource_type.props.subtype"
    ),
    "metadata.resource_type.id": _thesis_value_mapper("metadata.resource_type.id"),
    "metadata.resource_type.props.subtype": _thesis_value_mapper(
        "metadata.resource_type.props.subtype"
    ),
    "metadata.related_identifiers.resource_type.id": _thesis_value_mapper(
        "metadata.related_identifiers.resource_type.id"
    ),
    "resource_type.type": "metadata.resource_type.props.type",
    "access_right": "access.status",
    "alternate.identifier": "metadata.identifiers.identifier",
    "alternate.scheme": "metadata.identifiers.scheme",
    "communities": FieldValueMapper(
        "parent.communities.ids",
        word=word_communities,
        phrase=phrase_communities,
    ),
    "conceptdoi": FieldValueMapper("parent.pids.doi.identifier", word=word_doi),
    "conceptrecid": "parent.id",
    "created": "created",
    # Creators
    "creators.affiliation": "metadata.creators.affiliations.name",
    "creators.name": "metadata.creators.person_or_org.name",
    "creators.orcid": "metadata.creators.person_or_org.identifiers.identifier",
    "creators.gnd": "metadata.creators.person_or_org.identifiers.identifier",
    # Contributors
    "contributors.affiliation": "metadata.contributors.affiliations.name",
    "contributors.name": "metadata.contributors.person_or_org.name",
    "contributors.orcid": "metadata.contributors.person_or_org.identifiers.identifier",
    "contributors.gnd": "metadata.contributors.person_or_org.identifiers.identifier",
    "contributors.type": "metadata.contributors.role.id",
    "description": "metadata.description",
    "doi": FieldValueMapper("pids.doi.identifier", word=word_doi),
    "embargodate": "access.embargo.until",
    "grants.code": "metadata.funding.award.number",
    "grants.acronym": "metadata.funding.award.acronym",
    "grants.program": "metadata.funding.award.program",
    "grants.title": "metadata.funding.award.title.en",
    # owner
    "owners": "parent.access.owned_by.user",
    # TODO: Add `grants.funder.*` mappings
    "grants.funder.doi": FieldValueMapper(
        "metadata.funding.funder.identifiers.identifier", word=word_doi
    ),
    "grants.funder.name": "metadata.funding.funder.name",
    "keywords": "metadata.subjects.subject",
    "language": "metadata.languages.id",
    "license.identifier": "metadata.rights.id",
    "license.url": "metadata.rights.props.url",
    "publicationdate": "metadata.publication_date",
    "publication_date": "metadata.publication_date",
    "recid": "id",
    "related.identifier": "metadata.related_identifiers.identifier",
    "related.scheme": "metadata.related_identifiers.scheme",
    "related.relation": "metadata.related_identifiers.relation_type.id",
    "title": "metadata.title",
    "type": "metadata.resource_type.props.type",
    "version": "versions.index",
    # journal custom field mappings
    "journal.title": r"custom_fields.journal\:journal.title",
    "journal.pages": r"custom_fields.journal\:journal.pages",
    "journal.volume": r"custom_fields.journal\:journal.volume",
    "journal.issn": r"custom_fields.journal\:journal.issn",
    # meeting custom field mappings
    "meeting.title": r"custom_fields.meeting\:meeting.title",
    "meeting.acronym": r"custom_fields.meeting\:meeting.acronym",
    "meeting.dates": r"custom_fields.meeting\:meeting.dates",
    "meeting.place": r"custom_fields.meeting\:meeting.place",
    "meeting.url": r"custom_fields.meeting\:meeting.url",
    "meeting.session": r"custom_fields.meeting\:meeting.session",
    "meeting.session_part": r"custom_fields.meeting\:meeting.session_part",
    "part_of.title": r"custom_fields.imprint\:imprint.title",
    "part_of.pages": r"custom_fields.imprint\:imprint.pages",
    # imprint custom field mappings
    "imprint.isbn": r"custom_fields.imprint\:imprint.isbn",
    "imprint.place": r"custom_fields.imprint\:imprint.place",
    "imprint.publisher": r"custom_fields.imprint\:imprint.publisher",
    # notes custom field mappings
    "notes": "metadata.additional_descriptions.description",
    # thesis custom field mappings
    "thesis.university": r"custom_fields.thesis\:thesis.university",
    # Files
    "filecount": "files.count",
    "filename": "files.entries.key",
    "filetype": "files.types",
    "filesize": "files.totalbytes",
    "size": "files.totalbytes",
    "_files.checksum": "files.entries.checksum",
    "_files.size": "files.entries.size",
    # New mappings
    "user": "parent.access.owned_by.user",
}
