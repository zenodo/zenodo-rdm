from invenio_rdm_migrator.streams import StreamDefinition
from invenio_rdm_migrator.streams.communities import CommunityCopyLoad
from invenio_rdm_migrator.streams.records import RDMRecordCopyLoad
from invenio_rdm_migrator.streams.users import UserCopyLoad

from .extract import JSONLExtract
from .transform import (
    ZenodoCommunityTransform,
    ZenodoToRDMRecordTransform,
    ZenodoUserTransform,
)


CommunitiesStreamDefinition = StreamDefinition(
    name="communities",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoCommunityTransform,
    load_cls=CommunityCopyLoad,
)

RecordStreamDefinition = StreamDefinition(
    name="records",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoToRDMRecordTransform,
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo to RDM records."""


UserStreamDefinition = StreamDefinition(
    name="users",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoUserTransform,
    load_cls=UserCopyLoad,
)
"""ETL stream for Zenodo to import users."""
