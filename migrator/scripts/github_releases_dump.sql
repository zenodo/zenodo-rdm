COPY (
  SELECT
    row_to_json(releases)
  FROM (
    SELECT
      gr.*,
      r.json->'recid' as recid
    FROM
      github_releases as gr
      JOIN records_metadata as r on gr.record_id = r.id
  ) as releases
) TO STDOUT;
