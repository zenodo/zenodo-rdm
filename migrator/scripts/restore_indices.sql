-- From https://www.postgresql.org/message-id/flat/877em2racj.fsf%40gmail.com#36a9eba4b16b8172e379b2a19f403939
DO
$$
DECLARE
  l_rec record;
BEGIN
  for l_rec IN SELECT indexdef FROM rdm_index_backup
  LOOP
     EXECUTE l_rec.indexdef;
  END LOOP;
END;
$$
