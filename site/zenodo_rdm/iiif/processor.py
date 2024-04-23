import datetime

from invenio_records_resources.services.files.processors import FileProcessor
from invenio_records_resources.services.uow import TaskOp

from zenodo_rdm.iiif.tasks import generate_zoomable_image


class TilesProcessor(FileProcessor):

    def __init__(self, valid_exts=["tif", "jpeg", "png"]):
        self.valid_exts = valid_exts

    def can_process(self, file_record):
        if file_record.file.ext in self.valid_exts:
            return True

    def process(self, file_record, uow):
        record = file_record.record
        uow.register(
            TaskOp(
                generate_zoomable_image,
                record_id=record["id"],
                file_key=file_record.key,
            )
        )
