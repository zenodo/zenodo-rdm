# SPDX-FileCopyrightText: 2024-2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Query parsers."""

import json
from fnmatch import fnmatchcase
from functools import cache

from invenio_access.permissions import system_permission
from invenio_communities.communities.records.models import CommunityMetadata
from invenio_db import db
from invenio_i18n import gettext as _
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.errors import QuerystringValidationError
from invenio_records_resources.services.records.queryparser import (
    FieldValueMapper,
    QueryParser,
    SearchFieldTransformer,
)
from invenio_search import current_search
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


INTERNAL_NOTES_FIELDS = (
    "internal_notes",
    "internal_notes.id",
    "internal_notes.note",
    "internal_notes.timestamp",
    "internal_notes.added_by",
    "internal_notes.added_by.user",
)
"""Indexed internal notes fields, which only the system process may search."""


def _targets_internal_notes(field_name):
    """Check if a field name, possibly with wildcards, can match internal notes."""
    field_name = field_name.replace("\\", "")
    return field_name.startswith("internal_notes") or any(
        fnmatchcase(field, field_name) for field in INTERNAL_NOTES_FIELDS
    )


def _term_values(node):
    """Yield the values of all words and phrases below a query node."""
    if isinstance(node, (Word, Phrase)):
        yield node.value.strip('"')
    for child in node.children:
        yield from _term_values(child)


class ZenodoSearchFieldTransformer(SearchFieldTransformer):
    """Search field transformer that keeps internal notes out of user queries.

    Upstream restricts the exact ``internal_notes.*`` field names through the
    search mapping. This also covers sub-fields, wildcard field names (e.g.
    ``*:term`` or ``*.note:term``) and ``_exists_`` checks on notes. Rejected
    queries fall back to a plain multi-match query on the default fields.
    """

    def visit_search_field(self, node, context):
        """Reject internal notes fields for callers other than the system."""
        targets_notes = _targets_internal_notes(node.name) or (
            node.name == "_exists_"
            and any(_targets_internal_notes(v) for v in _term_values(node.expr))
        )
        if targets_notes and not system_permission.allows(context["identity"]):
            raise QuerystringValidationError(
                _("Invalid search field: %(field_name)s.", field_name=node.name)
            )
        yield from super().visit_search_field(node, context)


@cache
def _mapping_default_fields(index_name):
    """Read the ``index.query.default_field`` setting of an index mapping."""
    with open(current_search.mappings[index_name]) as fp:
        return json.load(fp)["settings"]["index.query.default_field"]


class ZenodoDraftsQueryParser(QueryParser):
    """Query parser searching the records default fields on drafts.

    The drafts index does not define ``index.query.default_field``, so terms
    without a field would match every field, including internal notes. Use
    the records index default fields instead, unless ``fields`` is given.
    """

    def __init__(self, *args, **kwargs):
        """Initialise the parser."""
        super().__init__(*args, **kwargs)
        if not self._fields:
            index_name = current_rdm_records_service.record_cls.index._name
            self._fields = list(_mapping_default_fields(index_name))
            self.extra_params["fields"] = self._fields
