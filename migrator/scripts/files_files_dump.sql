COPY (
  SELECT
      id,
      created,
      updated,
      uri,
      'L' as storage_class,
      size,
      checksum,
      readable,
      writable,
      last_check_at,
      last_check
  FROM files_files
) TO STDOUT WITH (FORMAT csv);
