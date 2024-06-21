"""Generate IIIF tiles for a list of records.

Generated using the following SQL script:

```sql
\copy (

select
    p.pid_value as recid,
    p.object_uuid,
    count(case when rf.key ILIKE '%.gif' then 1 end) as gif_count,
    count(case when rf.key ILIKE '%.jp2' then 1 end) as jp2_count,
    count(case when rf.key ILIKE '%.jpeg' or rf.key ILIKE '%.jpg' then 1 end) as jpg_count,
    count(case when rf.key ILIKE '%.pdf' then 1 end) as pdf_count,
    count(case when rf.key ILIKE '%.png' then 1 end) as png_count,
    count(case when rf.key ILIKE '%.tif' or rf.key ILIKE '%.tiff' then 1 end) as tiff_count
  from
    pidstore_pid as p
    join rdm_records_files as rf on rf.record_id = p.object_uuid
  where
    p.pid_type = 'recid'
    and (
      -- TODO: Include GIF or not?
      rf.key ILIKE '%.gif'
      or rf.key ILIKE '%.jp2'
      or rf.key ILIKE '%.jpeg'
      or rf.key ILIKE '%.jpg'
      -- TODO: Include PDF or not?
      or rf.key ILIKE '%.pdf'
      or rf.key ILIKE '%.png'
      or rf.key ILIKE '%.tif'
      or rf.key ILIKE '%.tiff'
    )
group by p.pid_value, p.object_uuid
order by p.pid_value::int

) TO '/root/rec_iiif.csv' WITH (FORMAT CSV, HEADER)
```
"""
from invenio_rdm_records.proxies import current_rdm_records_service as service
from invenio_rdm_records.records.processors.tiles import TilesProcessor
from invenio_records_resources.services.files.processors.image import ImageMetadataExtractor
from invenio_records_resources.services.uow import UnitOfWork, RecordCommitOp
import sys
import csv


image_metadata_extractor = ImageMetadataExtractor()

def generate_iiif_tiles(recid):
    with UnitOfWork() as uow:
        record = service.record_cls.pid.resolve(recid)
        processor = TilesProcessor()
        # Call the processor on the record
        processor(None, record, uow=uow)
        uow.register(RecordCommitOp(record))

        # Calculate image dimensions for each supported image file
        # NOTE: This happens "synchronously", but VIPS is pretty fast and doesn't load
        # the entire image in memory.
        for file_record in record.files.values():
            if image_metadata_extractor.can_process(file_record):
                image_metadata_extractor.process(file_record)
                file_record.commit()
        uow.commit()



def process_csv(csv_path):
    with open(csv_path, 'r') as fin:
        reader = csv.reader(fin)
        for recid, *_ in reader:
            print(f"Processing record {recid}")
            try:
                generate_iiif_tiles(recid)
                print(f"Record {recid} processed")
            except Exception as e:
                print(f"Error processing record {recid}: {e}")

if __name__ == "__main__":
    csv_path = sys.argv[1]
    process_csv(csv_path)
