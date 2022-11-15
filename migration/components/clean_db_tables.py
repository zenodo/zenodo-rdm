from invenio_rdm_records.records.models import (
    RDMParentMetadata,
    RDMDraftMetadata,
    RDMRecordMetadata,
    RDMVersionsState,
)
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

PersistentIdentifier.query.filter(
    PersistentIdentifier.pid_type.in_(("recid", "doi", "oai")),
    PersistentIdentifier.object_type == "rec",
).delete()
RDMVersionsState.query.delete()
RDMRecordMetadata.query.delete()
RDMParentMetadata.query.delete()
RDMDraftMetadata.query.delete()
db.session.commit()
