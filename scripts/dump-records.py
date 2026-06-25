"""Dump records training data for the spam classifier."""

import csv
import gzip
import io
import re
import string
from datetime import datetime
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from flask import current_app
from invenio_app.factory import create_api
from invenio_search.proxies import current_search_client as client
from opensearch_dsl import Search
from xrootdpyfs import XRootDPyFS

emoji_pattern = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
    "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
    "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
    "\U00002700-\U000027BF"  # Dingbats
    "\U000024C2-\U0001F251"  # Enclosed characters
    "]+", flags=re.UNICODE)


def extract_emojis(text):
    """Extract emojis from the text."""
    # Emoji regex pattern
    return emoji_pattern.findall(text)


def links_stats(soup):
    """Extra number of links and their hosts."""
    # Parse description and look for links
    count = 0
    hosts = set()
    for link in soup.find_all('a'):
        count += 1
        hosts.add(urlparse(link.get('href')).hostname)
    return count, hosts


def make_fs(klass):
    baseurl = f"root://eosuser.cern.ch//eos/project/z/zenodo/Dumps/{klass}/"
    return XRootDPyFS(baseurl)


def truncate(text, max_length):
    # strip punctuation as well
    parts = text.strip().split(" ")
    if len(parts) >= max_length:
        parts = parts[:max_length]
    return ' '.join(parts)


def prepare_record(r):
    """Prepare a record"""
    # Label
    if r.parent.is_verified and r.is_published:
        label = 1  # ham
    elif r.is_deleted and r.tombstone.removal_reason.id == 'spam':
        label = 0  # spam
    else:
        return None

    # Record ids
    id = r.id

    # User info
    uid = r.parent.access.owned_by.user
    u = users_db.get(uid, None)
    if u is None:
        return None
    ustatus, udomain, udomainstatus = u

    # Text
    title = getattr(r.metadata, "title", "")
    soup = BeautifulSoup(getattr(r.metadata, "description", ""), 'html.parser')
    description = soup.get_text()
    text = truncate(title + description, 4000)

    # Exclude records with empty text
    if text.strip() == "":
        return None

    # Computed properties
    emojis = len(extract_emojis(title)) + len(extract_emojis(description))
    title_len = len(title)
    description_len = len(description)
    links, links_domains = links_stats(soup)

    # Files
    files = getattr(r.files, "count", 0)
    bytes = getattr(r.files, "totalbytes", 0)
    types = getattr(r.files, "types", [])

    # Todo detect language

    return [label, id, r.created, udomain, title_len, description_len, links, emojis, files, bytes, text, links_domains]


########################################################

app = create_api()
with app.app_context():
    idxprefix = current_app.config['SEARCH_INDEX_PREFIX']

    # Preload the users database
    t0 = datetime.now()
    print("Loading users database ...")
    users_db = {}
    s = Search(using=client, index=f'{idxprefix}users-user-v3.0.0').extra(track_total_hits=True)
    i = 0
    for u in s.scan():
        users_db[u.id] = (u.status, u.domain, u.domaininfo.status)
        i += 1
    print(f"... loaded {i} users")

    # Dump the records
    t1 = datetime.now()
    print("Writing records ...")
    query = f"(parent.is_verified:true AND is_published:true AND versions.is_latest:true) OR (is_deleted:true AND tombstone.removal_reason.id:spam AND versions.is_latest:true)"
    s = Search(using=client, index=f'{idxprefix}rdmrecords-records').extra(
        track_total_hits=True,
    ).query(
        "query_string",
        query=query,
    )

    # Writing the CSV and compressing at the same time
    fs = make_fs("records")
    stamp = datetime.now().date().isoformat()
    header = (
        "label",
        "id",
        "created",
        "domain",
        "title_len",
        "description_len",
        "links",
        "emojis",
        "files",
        "bytes",
        "text",
    )

    l_header = (
        "label",
        "id",
        "domain",
    )

    # TODO: write creators, links_domains in separate files.

    try:
        fp = fs.open(f"records-{stamp}.csv.gz", 'wb')
        gzfile = gzip.GzipFile(fileobj=fp, mode='wb')
        wrapper = io.TextIOWrapper(gzfile, encoding='utf-8', newline='')
        writer = csv.writer(wrapper)

        l_fp = fs.open(f"links-{stamp}.csv.gz", 'wb')
        l_gzfile = gzip.GzipFile(fileobj=l_fp, mode='wb')
        l_wrapper = io.TextIOWrapper(l_gzfile, encoding='utf-8', newline='')
        l_writer = csv.writer(l_wrapper)

        writer.writerow(header)
        l_writer.writerow(l_header)
        i = 0
        for r in s.scan():
            row = prepare_record(r)
            if row is not None:
                (label, id, created, udomain, title_len, description_len, links, emojis, files, bytes, text, links_domains) = row
                writer.writerow((label, id, created, udomain, title_len, description_len, links, emojis, files, bytes, text))
                i += 1
                if i % 100000 == 0:
                    print("...", i)
                if links_domains:
                    for l in links_domains:
                        l_writer.writerow([label,id,l])

        print(f"... wrote {i} records")
    finally:
        wrapper.close()
        gzfile.close()
        fp.close()

        l_wrapper.close()
        l_gzfile.close()
        l_fp.close()

    t2 = datetime.now()
    print("Loading users", t1-t0)
    print("Writing records", t2-t1)
