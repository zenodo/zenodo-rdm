"""Zenodo snippets for admins.

WARNING: these should be used with care as they are actions to be done from users
with superuser access! They should be deleted once they are integrated via UI options
"""


from invenio_access.permissions import system_identity
from invenio_rdm_records.proxies import current_rdm_records_service


def set_record_quota(id, quota_size, max_file_size=None, notes=None):
    """Util method to set a file quota for specific record."""
    return current_rdm_records_service.set_quota(
        system_identity,
        id,
        quota_size=quota_size,
        max_file_size=max_file_size,
        notes=notes,
    )


def set_user_quota(id, quota_size, max_file_size=None, notes=None):
    """Util method to set a file quota for specific user."""
    return current_rdm_records_service.set_quota(
        system_identity,
        id,
        quota_size=quota_size,
        max_file_size=max_file_size,
        notes=notes,
    )


def delete_record(id, data):
    """Util method to delete a specific record."""
    return current_rdm_records_service.delete_record(system_identity, id, data=data)


def restore_record(id):
    """Util method to restore a specific record."""
    return current_rdm_records_service.restore_record(system_identity, id)
