import sys
from datetime import datetime

from .extract import JSONLExtract
from .load import PostgreSQLCopyLoad
from .transform import ZenodoToRDMRecordTransform

# Usage
# python migration/run.py records-dump-2022-11-08.jsonl


class Stream:
    """ETL stream"""

    def __init__(self, extract, transform, load):
        """Constructor."""
        self.extract = extract
        self.transform = transform
        self.load = load

    def run(self, cleanup=False):
        """Run ETL stream."""
        start_time = datetime.now()
        print(f"Started workflow {start_time.isoformat()}")

        extract_gen = self.extract.run()
        transform_gen = self.transform.run(extract_gen)
        self.load.run(transform_gen, cleanup=cleanup)
        
        end_time = datetime.now()
        print(f"Ended workflow {end_time.isoformat()}")

        print(f"Total duration: {end_time - start_time}")

if __name__ == "__main__":

    filename = sys.argv[1]
    cleanup = len(sys.argv) > 2  # if there is something we assume is True/--cleanup
    stream = Stream(
        extract=JSONLExtract(filename),
        transform=ZenodoToRDMRecordTransform(),
        load=PostgreSQLCopyLoad(),
    )
    
    stream.run(cleanup=cleanup)
