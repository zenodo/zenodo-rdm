"""Zenodo legacy REST API quickstart flow.

See https://developers.zenodo.org/#quickstart-upload.
"""

from io import BytesIO

import requests

token = "CHANGE_ME"
auth_headers = {
    "Authorization": f"Bearer {token}",
}

headers = {
    **auth_headers,
    "Content-Type": "application/json",
}

files_headers = {
    **auth_headers,
    "Content-Type": "application/octet-stream",
}

base_url = "https://localhost:5000"

res_create = requests.post(
    f"{base_url}/api/deposit/depositions",
    json={},
    headers=headers,
    verify=False,
)
assert res_create.status_code == 201

bucket_url = res_create.json()["links"]["bucket"]
res_file_upload = requests.put(
    f"{bucket_url}/test1.txt",
    data=BytesIO(b"example file"),
    headers=files_headers,
    verify=False,
)
assert res_file_upload.status_code == 200

# Old-style file upload
files_url = res_create.json()["links"]["files"]
data = {"name": "test2.txt"}
files = {"file": BytesIO(b"example file")}
res_file_upload = requests.post(
    files_url,
    headers=auth_headers,
    data=data,
    files=files,
    verify=False,
)
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
    verify=False,
)
assert res_update.status_code == 200

publish_url = res_create.json()["links"]["publish"]
res_publish = requests.post(
    publish_url,
    headers=headers,
    verify=False,
)
assert res_publish.status_code == 202
