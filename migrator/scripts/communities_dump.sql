COPY (
    WITH last_featured_comms AS (
        SELECT
            id_community as id,
            MAX(start_date) as start_date,
            MAX(created) as created,
            MAX(updated) as updated
        FROM communities_featured_community AS fc
        GROUP BY id_community
    )
    SELECT
        row_to_json(communities)
    FROM
        (
            SELECT
                c.*,
                CASE
                    WHEN fc.start_date IS NULL THEN FALSE
                    ELSE TRUE
                END as is_featured,
                fc.start_date as featured_start_date,
                fc.created as featured_created,
                fc.updated as featured_updated,
                ff.id as logo_file_id
            FROM
                communities_community as c
                LEFT OUTER JOIN last_featured_comms as fc ON c.id = fc.id
                LEFT OUTER JOIN files_object as fo ON
                    fo.key = c.id || '/logo.' || c.logo_ext
                    AND c.logo_ext IS NOT NULL
                    AND fo.bucket_id = '00000000-0000-0000-0000-000000000000'
                    AND fo.is_head
                LEFT OUTER JOIN files_files as ff ON fo.file_id = ff.id
            WHERE
                c.deleted_at IS NULL
        ) as communities
) TO STDOUT;
