
from invenio_rdm_migrator.streams import StreamDefinition
from invenio_rdm_migrator.streams.records.load import RDMRecordCopyLoad

from extract import JSONLExtract
from transform import ZenodoToRDMRecordTransform


RecordStreamDefinition = StreamDefinition(
    name="records",
    extract_cls=JSONLExtract,
    transform_cls=ZenodoToRDMRecordTransform,
    load_cls=RDMRecordCopyLoad,
)
"""ETL stream for Zenodo to RDM records."""
