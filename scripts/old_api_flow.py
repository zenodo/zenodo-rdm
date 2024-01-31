"""Zenodo legacy REST API quickstart flow.

See https://developers.zenodo.org/#quickstart-upload.
"""
from io import BytesIO

import requests

TOKEN = "CHANGE_ME"
BASE_URL = "https://127.0.0.1:5000"

headers = {"Content-Type": "application/json"}
files_headers = {"Content-Type": "application/octet-stream"}
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {TOKEN}"})
session.verify = False


res_create = requests.post(
    f"{BASE_URL}/api/deposit/depositions",
    json={},
    headers=headers,
)
assert res_create.status_code == 201

bucket_url = res_create.json()["links"]["bucket"]
res_file_upload = requests.put(
    f"{bucket_url}/test1.txt",
    data=BytesIO(b"example file"),
    headers=files_headers,
)
assert res_file_upload.status_code == 201

# Old-style file upload
files_url = res_create.json()["links"]["files"]
data = {"name": "test2.txt"}
files = {"file": BytesIO(b"example file")}
res_file_upload = requests.post(files_url, data=data, files=files)
assert res_file_upload.status_code == 201

draft_url = res_create.json()["links"]["self"]
res_update = requests.put(
    draft_url,
    json={
        "metadata": {
            "title": "My first upload",
            "upload_type": "poster",
            "description": "This is my first upload",
            "creators": [{"name": "Doe, John", "affiliation": "Zenodo"}],
        }
    },
    headers=headers,
)
assert res_update.status_code == 200

publish_url = res_create.json()["links"]["publish"]
res_publish = requests.post(publish_url, headers=headers)
assert res_publish.status_code == 202

# Edit the record now
edit_url = res_publish.json()["links"]["edit"]
res_edit = requests.post(edit_url, headers=headers)
res_update = requests.put(
    draft_url,
    json={
        "metadata": {
            "title": "My first upload (edited)",
            "upload_type": "poster",
            "description": "This is my first upload",
            "creators": [{"name": "Doe, John", "affiliation": "Zenodo"}],
            "doi": "10.5072/zenodo.23779",
        }
    },
    headers=headers,
)
res_publish = requests.post(publish_url, headers=headers)
