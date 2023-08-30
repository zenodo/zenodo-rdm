COPY (
  SELECT
      id,
      created,
      updated,
      default_location,
      'L' as default_storage_class,
      size,
      quota_size,
      max_file_size,
      locked,
      deleted
  FROM files_bucket
) TO STDOUT WITH (FORMAT csv);
