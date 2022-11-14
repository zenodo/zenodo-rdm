import json
import sys
from datetime import datetime

from components.load import Load
from components.transform import Transform


EXTRACT_RECORDS_SQL = """
COPY (
    SELECT row_to_json(records)
    FROM (
        SELECT
            r.*, pr.index
        FROM records_metadata as r
            JOIN pidstore_pid
                ON pidstore_pid.object_uuid = r.id
            JOIN pidrelations_pidrelation as pr
                ON pidstore_pid.id = pr.child_id
        WHERE
            pidstore_pid.pid_type = 'recid' AND
            pidstore_pid.status = 'R' AND
            pidstore_pid.object_type = 'rec' AND
            r.updated >= (:last_load_timestamp)
    ) as records
) TO STDOUT;
"""


class Extract:
    def run(self):
        # TODO: Run and yield from the query above somehow?
        # yield from engine.execute(EXTRACT_RECORDS_SQL)
        pass


# NOTE: We need this to keep track of what Parent IDs we've already inserted in the
#       PIDs table.
PARENT_IDS_CACHE = {}
"""
{
    '<parent_pid>': {
        'id': <generated_parent_uuid>,
        'version': {
            'latest_index': 'record_index',
            'latest_id': 'record id',
        }
}
"""


# NOTE: Usage
#   gzip -dc records-dump-2022-11-08.jsonl.gz | head | sed 's/\\\\/\\/g' | python migration/run.py
# cat single-record.jsonl | sed 's/\\\\/\\/g' | python migration/run.py

if __name__ == "__main__":
    record_load = Load(stream="record", parent_cache=PARENT_IDS_CACHE)
    record_transform = Transform(stream="record")
    start_time = datetime.now().isoformat()
    print(f"Started workflow {start_time}")
    for idx, l in enumerate(sys.stdin.buffer):
        if idx % 100 == 0:
            print(datetime.now().isoformat(), idx)
        transform_result = record_transform.run(json.loads(l))
        print(idx, transform_result)
        # Write each result in csv tables:
        record_load.run(transform_result)
    end_time = datetime.now().isoformat()
    # populate version_state
    record_load.load_computed_tables()
    print(f"Ended workflow {end_time}")
