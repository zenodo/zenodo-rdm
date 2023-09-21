COPY (
    SELECT
        row_to_json(result)
    FROM
        (
            WITH deleted_records (
                id,
                removal_json,
                removal_date,
                version_id,
                recid,
                transaction_id
            ) AS (
                SELECT
                    r.id,
                    r.json as removal_json,
                    r.updated as removal_date,
                    r.version_id,
                    p.pid_value,
                    r.transaction_id
                FROM
                    records_metadata_version as r
                    JOIN pidstore_pid as p ON p.object_uuid = r.id
                WHERE
                    r.json IS NOT NULL
                    AND r.end_transaction_id IS NULL
                    AND p.pid_type = 'recid'
                    AND p.status = 'D'
                    AND p.object_type = 'rec'
            )
            SELECT
                r.id as id,
                r.json as json,
                r.created as created,
                dr.version_id as version_id,
                dr.recid as recid,
                dr.removal_date as updated,
                dr.removal_json as removal_json,
                dr.removal_date as removal_date
            FROM
                records_metadata_version as r
                JOIN deleted_records as dr ON r.id = dr.id
                AND r.end_transaction_id = dr.transaction_id
        ) as result
) TO STDOUT;
