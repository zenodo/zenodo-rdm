
from invenio_rdm_migrator.streams import Stream
from invenio_rdm_migrator.streams.records.load import RDMRecordCopyLoad

from extract import JSONLExtract
from transform import ZenodoToRDMRecordTransform


class RecordStream(Stream):
    """ETL stream for Zenodo to RDM records."""

    def __init__(self, filename, db_uri, output_path):
        """Constructor."""
        super().__init__(
            extract=JSONLExtract(filename),
            transform=ZenodoToRDMRecordTransform(),
            load=RDMRecordCopyLoad(db_uri, output_path),