# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Single-request file uploads for the legacy API.

In the legacy REST API, file uploads behave like a files-rest PUT on a specific file key
part of a draft. The key can be:

- a new file, in which case the file is created and attached to the record
- an existing file, in which case the file is replaced with the new content

We want to avoid keeping a database connection open for the whole transfer. This is
already implemented upstream in invenio-records-resources, but is built for the
three-step REST API (init + transfer + commit), which doesn't guarantee that the
"transfer" step is atomic. In particular, if the worker dies mid-transfer, the file is
left in a pending state, and the client has to clean it up. In the legacy API, we want
to avoid that, and either succeed or fail the whole request.

To solve this we stream into a "detached" FileInstance, and attach it at the very end in
one short locked transaction. We still go through the file service for init, permissions
check and commit. That means redoing/reimplementing some of the upstream preparation and
cleanup here. Handled failures delete the detached instance and its bytes, while a
killed request leaves them behind, unreferenced.
"""

from dataclasses import dataclass
from uuid import UUID

from flask import current_app
from invenio_db import db
from invenio_files_rest.errors import FileSizeError, InvalidKeyError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_files_rest.storage import FileStorage
from invenio_records_resources.services.errors import FailedFileUploadException
from invenio_records_resources.services.files.tasks import (
    cleanup_failed_upload,
    discard_failed_upload,
)
from invenio_records_resources.services.files.transfer import LOCAL_TRANSFER_TYPE
from invenio_records_resources.services.uow import UnitOfWork
from werkzeug.exceptions import ClientDisconnected


@dataclass(frozen=True)
class _PreparedFile:
    """The file instance an upload streams into before it is attached."""

    file_instance_id: UUID
    uri: str
    storage: FileStorage
    size_limit: int | FileSizeLimit | None


def upload_file(
    files_service, identity, pid_value, key, stream, content_length=None, replace=False
):
    """Upload a file, attaching it to the record only once its bytes are stored."""
    # Short transaction: create the detached file instance.
    prepared = _prepare_file(files_service, identity, pid_value, key, replace)

    # No transaction: stream the bytes to storage.
    try:
        _, size, checksum = prepared.storage.save(
            stream, size=content_length, size_limit=prepared.size_limit
        )
    except (ClientDisconnected, OSError) as error:
        _discard_file(prepared)
        raise FailedFileUploadException(
            recid=pid_value, file={"key": key}, file_key=key
        ) from error
    except Exception:
        _discard_file(prepared)
        raise

    # Short transaction: attach the file to the record.
    try:
        return _attach_file(
            files_service, identity, pid_value, key, replace, prepared, size, checksum
        )
    except Exception:
        _discard_file(prepared)
        raise


def _prepare_file(files_service, identity, pid_value, key, replace):
    """Create the file instance to stream into, without attaching it."""
    with UnitOfWork() as uow:
        record = files_service.record_cls.pid.resolve(pid_value, registered_only=False)
        files_service.require_permission(
            identity,
            "create_files",
            record=record,
            file_metadata={"key": key, "transfer": {"type": LOCAL_TRANSFER_TYPE}},
        )
        if not replace and key in record.files:
            raise InvalidKeyError(description=f"File with key {key} already exists.")
        bucket = record.files.bucket
        file_instance = FileInstance.create()
        storage = file_instance.storage(
            default_location=bucket.location.uri,
            default_storage_class=bucket.default_storage_class,
        )
        uri, _, _ = storage.initialize()
        file_instance.set_uri(uri, 0, None, readable=False, writable=True)
        prepared = _PreparedFile(
            file_instance_id=file_instance.id,
            uri=uri,
            storage=storage,
            size_limit=bucket.size_limit,
        )
        uow.commit()
    return prepared


def _attach_file(
    files_service, identity, pid_value, key, replace, prepared, size, checksum
):
    """Put the stored file under the key, replacing any existing file."""
    with UnitOfWork() as uow:
        record_cls = files_service.record_cls
        record = record_cls.pid.resolve(pid_value, registered_only=False)
        # Bucket first, in the same order as the upstream staged upload.
        db.session.query(Bucket).filter_by(
            id=record.files.bucket_id
        ).populate_existing().with_for_update().one()
        db.session.query(record_cls.model_cls).filter_by(
            id=record.id
        ).populate_existing().with_for_update().one()
        record = record_cls.pid.resolve(pid_value, registered_only=False)
        if replace and key in record.files:
            files_service.delete_file(identity, pid_value, key, uow=uow)
        files_service.init_files(identity, pid_value, [{"key": key}], uow=uow)
        record = record_cls.pid.resolve(pid_value, registered_only=False)
        files_service.require_permission(
            identity, "set_content_files", record=record, file_key=key
        )

        bucket = record.files.bucket
        if bucket.size_limit and size > bucket.size_limit:
            raise FileSizeError(description="File size limit exceeded.")
        file_instance = db.session.get(FileInstance, prepared.file_instance_id)
        file_instance.set_uri(prepared.uri, size, checksum)
        obj = record.files[key].object_version
        if obj is None:
            ObjectVersion.create(bucket, key).set_file(file_instance)
        else:
            # Staged init preallocates an empty file instance, ours replaces it.
            preallocated = obj.file
            obj.file = file_instance
            bucket.size += size
            db.session.flush()
            preallocated.delete()

        result = files_service.commit_file(identity, pid_value, key, uow=uow)
        uow.commit()
    return result


def _discard_file(prepared):
    """Remove the bytes of a failed upload, unless the file was attached.

    Runs in its own short transaction, after rolling back the failed one.
    """
    file_instance_id = str(prepared.file_instance_id)
    try:
        db.session.rollback()
        discard_failed_upload(file_instance_id, prepared.uri)
    except Exception:
        current_app.logger.exception("Failed to discard file of failed upload.")
        # Retried with backoff, for storage or database errors that pass.
        try:
            cleanup_failed_upload.delay(file_instance_id, prepared.uri)
        except Exception:
            current_app.logger.exception("Failed to schedule upload cleanup.")
