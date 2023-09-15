"""Zenodo snippets for admins.

WARNING: these should be used with care as they are actions to be done from users
with superuser access! They should be deleted once they are integrated via UI options
"""


from invenio_db import db
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.records import RDMRecord

from zenodo_rdm.legacy.requests.utils import submit_community_manage_record_request


def create_community_manage_record_request(record_id):
    """Util method to create a community manage record request."""

    # add a permission flag to db (make record a legacy one)
    db_record = RDMRecord.get_record(record_id)
    db_record.parent.permission_flags = {"can_community_manage_record": True}
    db_record.parent.commit()
    db.session.commit()

    current_rdm_records_service.indexer.index(db_record)

    # get record owner
    rec_owner = db_record.parent.access.owned_by.owner_id

    # create and submit a request
    return submit_community_manage_record_request(rec_owner)
