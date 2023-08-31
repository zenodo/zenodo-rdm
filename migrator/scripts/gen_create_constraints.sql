-- From https://blog.hagander.net/automatically-dropping-and-creating-constraints-131/
SELECT
  'ALTER TABLE "'||nspname||'"."'||relname||'" ADD CONSTRAINT "'||conname||'" '||pg_get_constraintdef(pg_constraint.oid)||';'
FROM pg_constraint
  INNER JOIN pg_class ON conrelid=pg_class.oid
  INNER JOIN pg_namespace ON pg_namespace.oid=pg_class.relnamespace
WHERE
  nspname = 'public'
ORDER BY
  CASE WHEN contype='f' THEN 0 ELSE 1 END DESC,
  contype DESC,
  nspname DESC,
  relname DESC,
  conname DESC;
