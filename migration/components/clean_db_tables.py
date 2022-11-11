from invenio_rdm_records.records.models import RDMParentMetadata
from invenio_records.models import RecordMetadata
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

[db.session.delete(item) for item in RecordMetadata.query.all()]
db.session.commit()
[db.session.delete(item) for item in RDMParentMetadata.query.all()]
db.session.commit()
[db.session.delete(item) for item in PersistentIdentifier.query.all()]
db.session.commit()
