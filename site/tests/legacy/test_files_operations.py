# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test legacy REST API file operations on both endpoint variants.

Covers ``/api/deposit/depositions/<id>/files`` (old-style deposit files API)
and ``/api/files/<bucket_id>/<key>`` (Files-REST API).
"""

from io import BytesIO

DEPOSIT_DATA = {
    "metadata": {
        "upload_type": "dataset",
        "title": "Legacy files operations",
        "creators": [{"name": "Doe, John"}],
        "publication_date": "2020-01-01",
        "description": "Legacy files operations test",
        "access_right": "open",
    }
}


def test_deposit_files_operations(client, deposit_url, headers, uploader):
    """Upload, list, read and delete files via /api/deposit/depositions."""
    client = uploader.api_login(client)
    res = client.post(deposit_url, json=DEPOSIT_DATA, headers=headers)
    assert res.status_code == 201, res.json
    files_url = res.json["links"]["files"]

    # Upload two files
    res = client.post(
        files_url,
        data={"name": "one.txt", "file": (BytesIO(b"one"), "one.txt")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 201, res.json
    file_one = res.json
    assert file_one["filename"] == "one.txt"
    assert file_one["filesize"] == 3
    assert file_one["checksum"] == "f97c5d29941bfb1b2fdab0874906ab82"
    assert {"self", "download"} <= file_one["links"].keys()

    res = client.post(
        files_url,
        data={"name": "two.txt", "file": (BytesIO(b"two"), "two.txt")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 201, res.json
    file_two = res.json

    # List files
    res = client.get(files_url, headers=headers)
    assert res.status_code == 200
    assert sorted(f["filename"] for f in res.json) == ["one.txt", "two.txt"]

    # Read a single file
    res = client.get(file_one["links"]["self"], headers=headers)
    assert res.status_code == 200
    assert res.json["id"] == file_one["id"]
    assert res.json["filename"] == "one.txt"
    assert res.json["checksum"] == "f97c5d29941bfb1b2fdab0874906ab82"

    # Delete a file
    res = client.delete(file_one["links"]["self"], headers=headers)
    assert res.status_code == 204
    assert res.data == b""

    # Reading and deleting it again is a 404
    res = client.get(file_one["links"]["self"], headers=headers)
    assert res.status_code == 404
    res = client.delete(file_one["links"]["self"], headers=headers)
    assert res.status_code == 404

    # Listing reflects the deletion
    res = client.get(files_url, headers=headers)
    assert res.status_code == 200
    assert [f["filename"] for f in res.json] == ["two.txt"]
    assert res.json[0]["id"] == file_two["id"]


def test_files_rest_operations(client, deposit_url, headers, files_headers, uploader):
    """Upload, list, download and delete files via /api/files/<bucket_id>."""
    client = uploader.api_login(client)
    res = client.post(deposit_url, json=DEPOSIT_DATA, headers=headers)
    assert res.status_code == 201, res.json
    bucket_url = res.json["links"]["bucket"]

    # Upload a file
    res = client.put(
        f"{bucket_url}/data.txt",
        headers=files_headers,
        data=BytesIO(b"1, 2, 3"),
    )
    assert res.status_code == 201, res.json
    data = res.json
    assert {"created", "updated"} <= data.keys()
    assert data["version_id"]
    assert data["key"] == "data.txt"
    assert data["size"] == 7
    assert data["checksum"] == "md5:66ce05ea43c73b8e33c74c12d0371bc9"
    assert data["mimetype"] == "text/plain"
    assert data["is_head"] is True
    assert data["delete_marker"] is False
    assert {"self", "uploads", "version"} <= data["links"].keys()

    # Download the file
    res = client.get(f"{bucket_url}/data.txt")
    assert res.status_code == 200
    assert res.data == b"1, 2, 3"

    # Overwrite the same key (delete + recreate under the hood)
    res = client.put(
        f"{bucket_url}/data.txt",
        headers=files_headers,
        data=BytesIO(b"4, 5, 6, 7"),
    )
    assert res.status_code == 201, res.json
    assert res.json["size"] == 10
    assert res.json["checksum"] == "md5:eaf1424a3bb9fafc4c7bb85c75806fd5"

    res = client.get(f"{bucket_url}/data.txt")
    assert res.status_code == 200
    assert res.data == b"4, 5, 6, 7"

    # List files in the bucket (Files-REST style "contents" envelope)
    res = client.get(bucket_url, headers=headers)
    assert res.status_code == 200, res.text
    contents = res.json["contents"]
    assert len(contents) == 1
    assert contents[0]["key"] == "data.txt"
    assert contents[0]["size"] == 10
    assert contents[0]["checksum"] == "md5:eaf1424a3bb9fafc4c7bb85c75806fd5"
    assert contents[0]["is_head"] is True
    assert {"self", "uploads", "version"} <= contents[0]["links"].keys()

    # Delete the file (regression: serializing the empty 204 body crashed
    # with "TypeError: string indices must be integers")
    res = client.delete(f"{bucket_url}/data.txt", headers=headers)
    assert res.status_code == 204, res.text
    assert res.data == b""

    # Downloading and deleting it again is a 404
    res = client.get(f"{bucket_url}/data.txt")
    assert res.status_code == 404
    res = client.delete(f"{bucket_url}/data.txt", headers=headers)
    assert res.status_code == 404
