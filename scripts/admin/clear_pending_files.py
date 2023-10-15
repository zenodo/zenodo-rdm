"""
Usage:
    export RDMTOK=....
    python3 clear_pending_files.py <id>
"""

import requests
import os, argparse

parser = argparse.ArgumentParser(description="Clear stuck files from UI uploader")
parser.add_argument("ids", nargs="*", help="Record IDs to clear")

args = parser.parse_args()

# Get access token as environment variable
token = os.environ["RDMTOK"]

url = "https://zenodo.org/api/records"

headers = {
    "Authorization": "Bearer %s" % token,
    "Content-type": "application/json",
}

for idv in args.ids:
    response = requests.get(f"{url}/{idv}/draft/files", headers=headers)
    entries = response.json()["entries"]
    for entry in entries:
        if entry["status"] == "pending":
            response = requests.delete(entry["links"]["self"], headers=headers)
            if response.status_code != 204:
                print(response.text)
                exit()
