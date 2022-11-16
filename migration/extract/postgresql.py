from .base import Extract

class PostgreSQLExtract(Extract):
    """Data extraction from PostgreSQL databases."""

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

    def run(self):
        """Yield one row at a time."""
        # yield from engine.execute(EXTRACT_RECORDS_SQL)
        pass
