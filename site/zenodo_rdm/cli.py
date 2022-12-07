import click

from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_rdm_records.records.models import (
    RDMParentCommunity,
    RDMRecordMetadata,
    RDMDraftMetadata,
    RDMVersionsState,
    RDMFileDraftMetadata,
    RDMFileRecordMetadata,
)
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records.api import RDMRecord, RDMDraft
from invenio_requests.records.models import RequestMetadata
from invenio_requests.records.api import Request
from invenio_requests.proxies import current_requests_service
from invenio_pidstore.models import PersistentIdentifier
from invenio_db import db


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
    help="A command to delete a record by giving the pid to delete. This is a temporary solution until the deletion mechanism is implemented in service layer.",
)
@with_appcontext
def delete_record(recid):
    """Custom script to delete a record.

    A command to delete a record by giving the pid to delete. **This is a temporary solution** until the deletion mechanism is implemented in service layer.
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
