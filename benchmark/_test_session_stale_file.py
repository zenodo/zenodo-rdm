import os, time
import common

common.SESSION_CACHE_FILE.write_text("{}")
assert not common._session_cache_is_stale(), "fresh file should not be stale"

four_days_ago = time.time() - 4 * 86400
os.utime(common.SESSION_CACHE_FILE, (four_days_ago, four_days_ago))
assert common._session_cache_is_stale(), "4 day old file should be stale"
