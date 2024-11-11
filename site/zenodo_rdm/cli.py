# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Zenodo RDM cli commands."""

import csv

import click
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_communities.communities.records.api import Community
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.api import RDMDraft, RDMRecord
from invenio_rdm_records.records.models import (
    RDMDraftMetadata,
    RDMFileDraftMetadata,
    RDMFileRecordMetadata,
    RDMParentCommunity,
    RDMRecordMetadata,
    RDMVersionsState,
)
from invenio_requests.proxies import current_requests_service
from invenio_requests.records.api import Request
from invenio_requests.records.models import RequestMetadata

from zenodo_rdm.api import ZenodoRDMRecord
from zenodo_rdm.moderation.models import ModerationQuery
from zenodo_rdm.moderation.percolator import (
    create_percolator_index,
    get_percolator_index,
    index_percolate_query,
)


def _get_parent(record_model):
    parent_model = record_model.parent
    parent_id = str(parent_model.id)

    # Parent communities
    parent_communities_ids = [
        comm for comm in parent_model.json["communities"].get("ids", [])
    ]
    parent_communities = (
        RDMParentCommunity.query.filter(
            RDMParentCommunity.community_id.in_(parent_communities_ids)
        )
        .filter(RDMParentCommunity.record_id == parent_id)
        .all()
    )

    parent_pid = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_value == parent_model.json["id"]
    ).one()

    requests_ids = [comm.request_id for comm in parent_communities]
    requests = []
    if requests_ids:
        requests = Request.get_records(requests_ids)

    return (parent_model, parent_id, parent_pid, parent_communities, requests)


def _get_record(recid):
    # PID
    record_pid = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_value == recid
    ).one()
    record_id = str(record_pid.object_uuid)
    # Associated identifiers
    record_identifiers = [
        identifier
        for identifier in PersistentIdentifier.query.filter(
            PersistentIdentifier.object_uuid == record_id
        ).all()
        if identifier.pid_value != recid
    ]
    # Record
    record_model = RDMRecordMetadata.query.filter_by(id=record_id).one()
    rdm_record = RDMRecord.get_record(record_id)

    # Draft
    draft_model = RDMDraftMetadata.query.filter_by(id=record_id).one_or_none()
    rdm_draft = None
    if draft_model:
        rdm_draft = RDMDraft.get_record(record_id, with_deleted=True)

    return (
        record_pid,
        record_id,
        record_identifiers,
        record_model,
        rdm_record,
        draft_model,
        rdm_draft,
    )


def _get_version(recid, parent_id):
    record_version = RDMVersionsState.query.filter(
        RDMVersionsState.parent_id == parent_id
    ).one_or_none()
    # check how many versions exist
    all_versions = current_rdm_records_service.search_versions(
        system_identity,
        recid,
    ).to_dict()["hits"]

    latest_record_version_id = str(record_version.latest_id)

    return (record_version, latest_record_version_id, all_versions)


def _delete_files(record_id):
    # Delete files for the record
    record_files = RDMFileRecordMetadata.query.filter(
        RDMFileRecordMetadata.record_id == record_id
    ).all()
    draft_files = RDMFileDraftMetadata.query.filter(
        RDMFileDraftMetadata.record_id == record_id
    ).all()

    for _file in record_files + draft_files:
        db.session.delete(_file)


def _delete_identifiers(identifiers):
    # delete records identifiers e.g oai, doi
    for identifier in identifiers:
        db.session.delete(identifier)


def _cleanup_record(
    record_version,
    record_pid,
    record_model,
    draft_model,
    parent_model,
    parent_pid,
    parent_communities,
):
    # record is the last existing version
    db.session.delete(record_version)
    # delete record pid
    db.session.delete(record_pid)
    # delete record
    db.session.delete(record_model)
    # delete draft
    if draft_model:
        db.session.delete(draft_model)
    # delete parent record
    db.session.delete(parent_model)
    # delete parent pid
    db.session.delete(parent_pid)
    # delete a parent communities
    for comm in parent_communities:
        db.session.delete(comm)
        request_id = comm.request_id
        # use model here to take advantage of the cascade deletion of request events
        RequestMetadata.query.filter(RequestMetadata.id == request_id).delete()


def _delete_record_and_draft(record_pid, record_model, draft_model):
    # delete record pid
    db.session.delete(record_pid)
    db.session.delete(record_model)
    # delete draft
    if draft_model:
        db.session.delete(draft_model)


def _revert_record_to_previous_version(latest_version, all_versions):
    # record has previous versions, so let's revert to the previous one
    previous_record = all_versions["hits"][1]
    previous_record_pid = PersistentIdentifier.query.filter(
        PersistentIdentifier.pid_value == previous_record["id"]
    ).one()
    latest_version.latest_id = str(previous_record_pid.object_uuid)
    latest_version.latest_index = previous_record["versions"]["index"]
    db.session.add(latest_version)


@click.group()
def zenodo_admin():
    """Zenodo admin commands."""


@zenodo_admin.command("delete")
@click.option(
    "-r",
    "--recid",
    type=str,
    required=True,
    help="Delete a record by giving the pid to delete. This is a temporary solution until the deletion mechanism is implemented in service layer.",
)
@with_appcontext
def delete_record(recid):
    """Custom script to delete a record.

    a command to delete a record by giving the pid to delete. **This is a temporary solution** until the deletion mechanism is implemented in service layer.
    Usage: invenio zenodo-admin delete -r <recid>
    """
    # Record
    (
        record_pid,
        record_id,
        record_identifiers,
        record_model,
        rdm_record,
        draft_model,
        rdm_draft,
    ) = _get_record(recid)
    # Parent
    (parent_model, parent_id, parent_pid, parent_communities, requests) = _get_parent(
        record_model
    )
    # Version
    (record_version, latest_record_version_id, all_versions) = _get_version(
        recid, parent_id
    )

    with db.session.begin_nested():
        _delete_files(record_id)
        _delete_identifiers(record_identifiers)

        # Are we deleting the latest record version?
        if latest_record_version_id == record_id:
            if all_versions["total"] == 1:
                _cleanup_record(
                    record_version,
                    record_pid,
                    record_model,
                    draft_model,
                    parent_model,
                    parent_pid,
                    parent_communities,
                )
            else:
                # NOTE: the record versions index is not properly adjusted when you delete a record.
                # That means that records versions can have inconsistencies between them e.g version 1, version 3, version 7
                # if you delete intermediate records
                _revert_record_to_previous_version(record_version, all_versions)
                _delete_record_and_draft(record_pid, record_model, draft_model)
        else:
            _delete_record_and_draft(record_pid, record_model, draft_model)

    db.session.commit()

    # Delete record from index
    current_rdm_records_service.indexer.delete(rdm_record)
    if rdm_draft:
        current_rdm_records_service.draft_indexer.delete(rdm_draft)

    for req in requests:
        current_requests_service.indexer.delete(req)


@click.group()
def moderation_cli():
    """Moderation commands."""


@moderation_cli.group()
def queries_cli():
    """Moderation queries commands."""


@queries_cli.command("create-index")
@click.option(
    "-r",
    "--record-cls",
    type=click.Choice(["records", "communities"], case_sensitive=False),
    default="records",
    help="Record class to base the index on (default: records).",
)
@with_appcontext
def create_index(record_cls):
    """Command to create a percolator index for moderation queries."""
    record_cls = ZenodoRDMRecord if record_cls == "records" else Community

    try:
        create_percolator_index(record_cls)
        index_name = get_percolator_index(record_cls)
        click.secho(f"Percolator index '{index_name}' created successfully.")
    except Exception as e:
        click.secho(f"Error creating percolator index: {e}")


@queries_cli.command("add")
@click.option(
    "-r",
    "--record-cls",
    type=click.Choice(["records", "communities"], case_sensitive=False),
    default="records",
    help="Record class to base the query on (default: records).",
)
@click.option(
    "-q",
    "--query-string",
    help="The query string for the moderation query (optional if loading from CSV).",
)
@click.option(
    "-n",
    "--notes",
    help="Additional notes for the moderation query (optional if loading from CSV).",
)
@click.option(
    "-s",
    "--score",
    default=10,
    type=int,
    help="The score for the moderation query (optional if loading from CSV).",
)
@click.option(
    "-a",
    "--active",
    default=True,
    type=bool,
    help="Whether the query is active (optional if loading from CSV).",
)
@click.option(
    "-f",
    "--file",
    type=click.Path(exists=True, readable=True),
    help="Path to CSV file containing queries.",
)
@with_appcontext
def add_query(record_cls, query_string, notes, score, active, file):
    """Command to add a moderation query from CSV or directly and index it."""
    record_cls = ZenodoRDMRecord if record_cls == "records" else Community

    try:
        if file:
            add_queries_from_csv(file, record_cls)
        else:
            create_and_index_query(record_cls, query_string, notes, score, active)

        click.secho("Queries added and indexed successfully.")
    except Exception as e:
        click.secho(f"Error adding or indexing query: {e}")


def add_queries_from_csv(file_path, record_cls=ZenodoRDMRecord):
    """Load queries from a CSV file, add them to the database, and index them."""
    with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile)

        for row in csvreader:
            if row:
                query_string = row[0].strip().strip("'")
                notes = row[1].strip().strip("'") if len(row) > 1 else None
                score = int(row[2].strip()) if len(row) > 2 else 10  # Default score 10
                active = (
                    row[3].strip().lower() == "true" if len(row) > 3 else True
                )  # Default to True

                # Ensure to add query only if there's a query string
                if query_string:
                    create_and_index_query(
                        record_cls, query_string, notes, score, active
                    )


def create_and_index_query(record_cls, query_string, notes, score, active):
    """Create and index a single moderation query."""
    query = ModerationQuery.create(
        query_string=query_string, notes=notes, score=score, active=active
    )

    db.session.commit()
    index_percolate_query(record_cls, query.id, query_string, active, score, notes)
