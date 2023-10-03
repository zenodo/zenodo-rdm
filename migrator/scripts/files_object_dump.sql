COPY (
  SELECT
    version_id,
    created,
    updated,
    key,
    bucket_id,
    file_id,
    _mimetype,
    is_head
  FROM
    files_object
) TO STDOUT WITH (FORMAT binary);
