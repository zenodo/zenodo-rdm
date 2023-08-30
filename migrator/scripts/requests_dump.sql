COPY (
    SELECT row_to_json(requests)
    FROM (
        WITH active_communities AS (
            SELECT DISTINCT(id_community) FROM communities_community_record
                INNER JOIN communities_community ON id_community=id
                WHERE id_community NOT IN ('zenodo', 'ecfunded')
                    AND deleted_at IS NULL
        ), records_ir AS (
            SELECT
                cr.created,
                cr.updated,
                (r.json->>'conceptrecid')::character varying AS conceptrecid,
                (r.json->>'recid')::character varying AS recid,
                cr.id_community,
                (r.json#>>'{owners, 0}')::character varying AS owners,
                (r.json->>'title')::character varying AS title
            FROM records_metadata AS r INNER JOIN communities_community_record AS cr
                ON id_record = id
                WHERE id_community NOT IN ('zenodo', 'ecfunded')
                    AND r.json->>'conceptrecid' IS NOT NULL
        ), records_pid AS (
            SELECT
                records_ir.created,
                records_ir.updated,
                records_ir.id_community,
                records_ir.conceptrecid,
                records_ir.recid,
                pidstore_pid.id as pid_id,
                records_ir.owners,
                records_ir.title
            FROM pidstore_pid INNER JOIN records_ir
                ON pid_value=records_ir.recid
                WHERE pid_type='recid' AND status!= 'D'
        ), records_index AS (
            SELECT
                records_pid.created,
                records_pid.updated,
                records_pid.id_community,
                records_pid.conceptrecid,
                records_pid.recid,
                pr.index,
                records_pid.owners,
                records_pid.title
            FROM records_pid INNER JOIN pidrelations_pidrelation AS pr
                ON pid_id = pr.child_id
        ), concept_last_version AS (
            SELECT conceptrecid, MAX(index) as max_index
            FROM records_index GROUP BY conceptrecid
        ), active_records AS (
            SELECT
                created,
                updated,
                id_community,
                ri.conceptrecid,
                recid,
                owners,
                title
            FROM records_index AS ri INNER JOIN concept_last_version AS clv
            ON ri.conceptrecid = clv.conceptrecid AND index = max_index
        )
        SELECT
            ar.created,
            ar.updated,
            ac.id_community,
            ar.conceptrecid,
            ar.recid,
            ar.owners,
            ar.title
        FROM active_records AS ar INNER JOIN active_communities AS ac
            ON ar.id_community=ac.id_community
    ) as requests
) TO STDOUT;
