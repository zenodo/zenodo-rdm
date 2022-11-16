import sys
from datetime import datetime

from .extract import JSONLExtract
from .load import RDMRecordLoad
from .transform import RDMRecordTransform


# Usage
# python migration/run.py records-dump-2022-11-08.jsonl

if __name__ == "__main__":

    filename = sys.argv[1] # TODO: click?
    cleanup = len(sys.argv) > 2  # if there is something we assume is True/--cleanup
    extract = JSONLExtract(filename)
    record_transform = RDMRecordTransform()
    record_load = RDMRecordLoad()

    start_time = datetime.now()
    print(f"Started workflow {start_time.isoformat()}") # TODO: logging?
    extract_gen = extract.run()
    record_transform_gen = record_transform.run(extract_gen)
    record_load.run(record_transform_gen, cleanup=cleanup)
    end_time = datetime.now()
    print(f"Ended workflow {end_time.isoformat()}")

    print(f"Total duration: {end_time - start_time}")
