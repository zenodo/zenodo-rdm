# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later
"""Test legacy serializer file link generation."""

from zenodo_rdm.legacy.serializers.schemas import LegacySchema, ZenodoSchema


def test_serializers_generate_expected_file_links(test_app):
    """Serializers preserve slashes and encode spaces in file links."""
    api_url = test_app.config["SITE_API_URL"]
    obj = {
        "id": "12345",
        "links": {"files": f"{api_url}/records/12345/files"},
        "files": {
            "entries": {
                "project/report draft.pdf": {
                    "id": "file-1",
                    "key": "project/report draft.pdf",
                    "size": 7,
                    "checksum": "md5:0123456789abcdef0123456789abcdef",
                }
            }
        },
    }

    with test_app.app_context():
        legacy_file = LegacySchema().dump_files(obj)[0]
        zenodo_file = ZenodoSchema().dump_files(obj)[0]

    assert legacy_file["links"]["download"] == (
        f"{api_url}/records/12345/draft/files/project/report%20draft.pdf/content"
    )
    assert zenodo_file["links"]["self"] == (
        f"{api_url}/records/12345/files/project/report%20draft.pdf/content"
    )
