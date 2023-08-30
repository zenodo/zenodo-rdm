COPY (
    SELECT row_to_json(deposits)
    FROM (
        SELECT
            r.*
        FROM records_metadata as r
            JOIN pidstore_pid
                ON pidstore_pid.object_uuid = r.id
        WHERE
            pidstore_pid.pid_type = 'depid' AND
            pidstore_pid.status = 'R' AND
            pidstore_pid.object_type = 'rec'
    ) as deposits
) TO STDOUT;
