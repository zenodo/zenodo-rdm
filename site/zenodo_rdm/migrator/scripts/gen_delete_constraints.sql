-- From https://blog.hagander.net/automatically-dropping-and-creating-constraints-131/
SELECT
  'ALTER TABLE "'||nspname||'"."'||relname||'" DROP CONSTRAINT "'||conname||'";'
FROM pg_constraint
  INNER JOIN pg_class ON conrelid=pg_class.oid
  INNER JOIN pg_namespace ON pg_namespace.oid=pg_class.relnamespace
ORDER BY
  CASE WHEN contype='f' THEN 0 ELSE 1 END,
  contype,
  nspname,
  relname,
  conname;
