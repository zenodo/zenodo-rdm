from io import BytesIO

import requests

TOKEN = "CHANGE_ME"
BASE_URL = "https://127.0.0.1:5000"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/vnd.inveniordm.v1+json",
}
files_headers = {
    "Content-Type": "application/octet-stream",
}
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {TOKEN}"})
session.verify = False


res_create = session.post(f"{BASE_URL}/api/records", headers=headers)
assert res_create.status_code == 201

draft_url = res_create.json()["links"]["self"]
files_url = res_create.json()["links"]["files"]

res_file_init = session.post(files_url, json=[{"key": "test1.txt"}])
assert res_file_init.status_code == 201
content_url = res_file_init.json()["entries"][0]["links"]["content"]

res_file_upload = session.put(
    content_url,
    headers=files_headers,
    data=BytesIO(b"example file"),
)
assert res_file_upload.status_code == 201

commit_url = res_file_upload.json()["links"]["commit"]
res_file_commit = session.post(commit_url)

res_update = session.put(
    draft_url,
    json={
        "access": {"record": "public", "files": "public"},
        "metadata": {
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Brown",
                        "given_name": "Troy",
                        "type": "personal",
                    }
                },
            ],
            "publication_date": "2020-06-01",
            "resource_type": {"id": "image-photo"},
            "title": "A Romans story",
            "publisher": "Zenodo",
        },
    },
    headers=headers,
)
assert res_update.status_code == 200

publish_url = res_update.json()["links"]["publish"]
res_publish = session.post(publish_url, headers=headers)
assert res_publish.status_code == 202

# Edit the record now
res_edit = session.post(draft_url, headers=headers)
res_update = session.put(
    draft_url,
    json={
        "access": {"record": "public", "files": "public"},
        "pids": {"doi": res_edit.json()["pids"]["doi"]},
        "metadata": {
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Brown",
                        "given_name": "Troy",
                        "type": "personal",
                    }
                },
            ],
            "publication_date": "2020-06-01",
            "resource_type": {"id": "image-photo"},
            "title": "An Updated Romans story",
            "publisher": "Zenodo",
        },
    },
    headers=headers,
)
res_publish = session.post(publish_url, headers=headers)
