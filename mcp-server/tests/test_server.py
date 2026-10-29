# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the Zenodo MCP tools against a fake API."""

from conftest import RECORD

READ_TOOLS = {
    "zenodo_search_records",
    "zenodo_get_record",
    "zenodo_list_versions",
    "zenodo_list_files",
    "zenodo_search_communities",
    "zenodo_get_community",
    "zenodo_search_vocabulary",
}
WRITE_TOOLS = {
    "zenodo_create_draft",
    "zenodo_update_draft",
    "zenodo_upload_file",
    "zenodo_delete_draft_file",
    "zenodo_publish_draft",
    "zenodo_new_version",
    "zenodo_discard_draft",
}


async def tool_names(client):
    return {t.name for t in (await client.list_tools()).tools}


async def test_anonymous_server_is_read_only(make_client):
    async with make_client() as client:
        assert await tool_names(client) == READ_TOOLS


async def test_token_adds_write_tools(make_client):
    async with make_client(token="secret") as client:
        tools = (await client.list_tools()).tools
        names = {t.name for t in tools}
        assert names == READ_TOOLS | WRITE_TOOLS | {"zenodo_list_my_records"}
        by_name = {t.name: t for t in tools}
        assert by_name["zenodo_publish_draft"].annotations.destructive_hint is True
        assert by_name["zenodo_search_records"].annotations.read_only_hint is True


async def test_read_only_flag_hides_write_tools(make_client):
    async with make_client(token="secret", read_only=True) as client:
        assert await tool_names(client) == READ_TOOLS | {"zenodo_list_my_records"}


async def test_search_records(make_client, fake):
    fake.route("GET", "/api/records", body={"hits": {"total": 25, "hits": [RECORD]}})
    async with make_client() as client:
        result = await client.call_tool(
            "zenodo_search_records",
            {"query": "photometry", "resource_type": "dataset", "size": 10},
        )
    data = result.structured_content
    assert data["total"] == 25 and data["has_more"] is True
    rec = data["records"][0]
    assert rec["doi"] == "10.5281/zenodo.123"
    assert rec["concept_doi"] == "10.5281/zenodo.122"
    assert rec["description"] == "Photometry data"
    assert rec["creators"][0]["orcid"] == "0000-0000-0000-0001"
    request = fake.requests[0]
    assert request.url.params["resource_type"] == "dataset"
    assert "allversions" not in request.url.params
    assert request.headers["accept"] == "application/vnd.inveniordm.v1+json"
    assert "authorization" not in request.headers


async def test_search_in_community(make_client, fake):
    fake.route(
        "GET", "/api/communities/astro/records", body={"hits": {"total": 0, "hits": []}}
    )
    async with make_client() as client:
        result = await client.call_tool("zenodo_search_records", {"community": "astro"})
    assert result.structured_content["total"] == 0


async def test_get_record_by_doi_url(make_client, fake):
    fake.route("GET", "/api/records/123", body=RECORD)
    async with make_client() as client:
        result = await client.call_tool(
            "zenodo_get_record", {"record": "https://doi.org/10.5281/zenodo.123"}
        )
    assert result.structured_content["title"] == "Light curves of HD 128329"


async def test_files_use_plain_json(make_client, fake):
    fake.route(
        "GET",
        "/api/records/123/files",
        body={
            "enabled": True,
            "entries": [
                {
                    "key": "lc.csv",
                    "size": 10,
                    "checksum": "md5:x",
                    "links": {
                        "content": "https://zenodo.test/api/records/123/files/lc.csv/content"
                    },
                }
            ],
        },
    )
    async with make_client() as client:
        result = await client.call_tool("zenodo_list_files", {"record": "123"})
    assert result.structured_content["files"][0]["key"] == "lc.csv"
    assert fake.requests[0].headers["accept"] == "application/json"


async def test_bad_record_id_is_a_tool_error(make_client):
    async with make_client() as client:
        result = await client.call_tool("zenodo_get_record", {"record": "hello"})
    assert result.is_error
    assert "Could not read a Zenodo record id" in result.content[0].text


async def test_http_errors_are_explained(make_client, fake):
    fake.route("GET", "/api/records/9", status=429, body={"message": "Too many"})
    async with make_client() as client:
        result = await client.call_tool("zenodo_get_record", {"record": "9"})
    assert result.is_error
    assert "rate limit" in result.content[0].text


async def test_create_draft_builds_rdm_metadata(make_client, fake):
    fake.route("POST", "/api/records", status=201, body={**RECORD, "is_draft": True})
    async with make_client(token="secret") as client:
        result = await client.call_tool(
            "zenodo_create_draft",
            {
                "title": "My data",
                "resource_type": "dataset",
                "creators": [
                    {
                        "name": "Curie, Marie",
                        "orcid": "0000-0000-0000-0001",
                        "affiliation": "CERN",
                    },
                    {"name": "CERN", "type": "organizational"},
                ],
                "license": "cc-by-4.0",
                "keywords": ["astronomy"],
                "access": "restricted",
            },
        )
    assert not result.is_error
    (body,) = fake.sent("POST", "/api/records")
    meta = body["metadata"]
    assert meta["resource_type"] == {"id": "dataset"}
    assert meta["rights"] == [{"id": "cc-by-4.0"}]
    assert meta["subjects"] == [{"subject": "astronomy"}]
    assert meta["publisher"] == "Zenodo"
    person, org = meta["creators"]
    assert person["person_or_org"] == {
        "type": "personal",
        "family_name": "Curie",
        "given_name": "Marie",
        "identifiers": [{"scheme": "orcid", "identifier": "0000-0000-0000-0001"}],
    }
    assert person["affiliations"] == [{"name": "CERN"}]
    assert org["person_or_org"] == {"type": "organizational", "name": "CERN"}
    assert body["access"] == {"record": "public", "files": "restricted"}
    assert fake.requests[0].headers["authorization"] == "Bearer secret"


async def test_update_published_record_opens_edit_draft(make_client, fake):
    fake.route("POST", "/api/records/123/draft", body={**RECORD, "is_draft": True})
    fake.route("PUT", "/api/records/123/draft", body={**RECORD, "is_draft": True})
    async with make_client(token="secret") as client:
        result = await client.call_tool(
            "zenodo_update_draft", {"record": "123", "title": "New title"}
        )
    assert not result.is_error
    (body,) = fake.sent("PUT", "/api/records/123/draft")
    assert body["metadata"]["title"] == "New title"
    # untouched fields are kept and read-only keys are not sent back
    assert body["metadata"]["rights"] == [{"id": "cc-by-4.0"}]
    assert "stats" not in body and "links" not in body


async def test_upload_file_three_steps(make_client, fake, tmp_path):
    path = tmp_path / "light curve.csv"
    path.write_bytes(b"t,flux\n0,1\n")
    base = "/api/records/123/draft/files"
    fake.route("POST", base, status=201, body={})
    fake.route("PUT", f"{base}/light curve.csv/content", body={})
    fake.route(
        "POST",
        f"{base}/light curve.csv/commit",
        body={"key": "light curve.csv", "size": 12, "status": "completed"},
    )
    async with make_client(token="secret") as client:
        result = await client.call_tool(
            "zenodo_upload_file", {"record": "123", "file_path": str(path)}
        )
    assert not result.is_error, result.content
    assert result.structured_content["file"]["status"] == "completed"
    assert fake.sent("POST", base) == [[{"key": "light curve.csv"}]]
    put = next(r for r in fake.requests if r.method == "PUT")
    assert put.content == b"t,flux\n0,1\n"
    assert "light%20curve.csv" in str(put.url)


async def test_upload_missing_file(make_client, tmp_path):
    async with make_client(token="secret") as client:
        result = await client.call_tool(
            "zenodo_upload_file",
            {"record": "123", "file_path": str(tmp_path / "nope.csv")},
        )
    assert result.is_error and "No file at" in result.content[0].text


async def test_publish(make_client, fake):
    fake.route(
        "POST", "/api/records/123/draft/actions/publish", status=202, body=RECORD
    )
    async with make_client(token="secret") as client:
        result = await client.call_tool("zenodo_publish_draft", {"record": "123"})
    assert result.structured_content["published"]["doi"] == "10.5281/zenodo.123"


async def test_publish_to_community_submits_review(make_client, fake):
    fake.route("GET", "/api/communities/astro", body={"id": "uuid-1", "slug": "astro"})
    fake.route("PUT", "/api/records/123/draft/review", body={})
    fake.route(
        "POST",
        "/api/records/123/draft/actions/submit-review",
        body={"status": "submitted"},
    )
    async with make_client(token="secret") as client:
        result = await client.call_tool(
            "zenodo_publish_draft",
            {"record": "123", "community": "astro", "comment": "Please add"},
        )
    assert result.structured_content["request_status"] == "submitted"
    (review,) = fake.sent("PUT", "/api/records/123/draft/review")
    assert review == {
        "receiver": {"community": "uuid-1"},
        "type": "community-submission",
    }
    assert not fake.sent("POST", "/api/records/123/draft/actions/publish")


async def test_new_version_imports_files(make_client, fake):
    fake.route(
        "POST", "/api/records/123/versions", status=201, body={**RECORD, "id": "124"}
    )
    fake.route(
        "POST", "/api/records/124/draft/actions/files-import", status=201, body={}
    )
    async with make_client(token="secret") as client:
        result = await client.call_tool("zenodo_new_version", {"record": "123"})
    assert result.structured_content["draft"]["id"] == "124"
    assert fake.sent("POST", "/api/records/124/draft/actions/files-import")


async def test_token_not_leaked_in_errors(make_client, fake):
    fake.route(
        "POST",
        "/api/records/1/draft/actions/publish",
        status=403,
        body={"message": "Forbidden"},
    )
    async with make_client(token="super-secret-token") as client:
        result = await client.call_tool("zenodo_publish_draft", {"record": "1"})
    assert result.is_error
    assert "super-secret-token" not in result.content[0].text
    assert "deposit:actions" in result.content[0].text


async def test_community_path_traversal_rejected(make_client, fake):
    async with make_client(token="secret") as client:
        for tool, args in [
            ("zenodo_get_community", {"community": "../../admin"}),
            ("zenodo_search_records", {"community": "x/../../user"}),
            ("zenodo_publish_draft", {"record": "1", "community": ".."}),
        ]:
            result = await client.call_tool(tool, args)
            assert result.is_error and "Invalid community" in result.content[0].text
    assert fake.requests == []


async def test_dot_dot_filename_cannot_discard_draft(make_client, fake):
    async with make_client(token="secret") as client:
        result = await client.call_tool(
            "zenodo_delete_draft_file", {"record": "1", "filename": ".."}
        )
    assert result.is_error
    assert fake.requests == []


async def test_upload_dir_restriction(fake, tmp_path):
    import httpx
    from mcp import Client

    from zenodo_mcp.client import Settings
    from zenodo_mcp.server import create_server

    allowed = tmp_path / "allowed"
    allowed.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_bytes(b"x")
    settings = Settings(
        base_url="https://zenodo.test", token="t", upload_dir=allowed.resolve()
    )
    server = create_server(settings, transport=httpx.MockTransport(fake.handler))
    async with Client(server) as client:
        for path in (secret, allowed / ".." / "secret.txt"):
            result = await client.call_tool(
                "zenodo_upload_file", {"record": "1", "file_path": str(path)}
            )
            assert result.is_error and "ZENODO_UPLOAD_DIR" in result.content[0].text
    assert fake.requests == []


async def test_update_sends_vocabulary_ids_only(make_client, fake):
    expanded = {
        **RECORD,
        "is_draft": True,
        "metadata": {
            **RECORD["metadata"],
            "resource_type": {"id": "dataset", "title": {"en": "Dataset"}},
            "rights": [
                {
                    "id": "cc-by-4.0",
                    "title": {"en": "Creative Commons Attribution 4.0"},
                    "icon": "cc-by-icon",
                    "props": {"url": "https://creativecommons.org/licenses/by/4.0/"},
                },
                {"title": {"en": "Custom license"}, "link": "https://example.org"},
            ],
            "languages": [{"id": "eng", "title": {"en": "English"}}],
        },
    }
    fake.route("GET", "/api/records/123/draft", body=expanded)
    fake.route("PUT", "/api/records/123/draft", body=expanded)
    async with make_client(token="secret") as client:
        await client.call_tool("zenodo_update_draft", {"record": "123", "version": "2"})
    (body,) = fake.sent("PUT", "/api/records/123/draft")
    meta = body["metadata"]
    assert meta["rights"] == [
        {"id": "cc-by-4.0"},
        {"title": {"en": "Custom license"}, "link": "https://example.org"},
    ]
    assert meta["resource_type"] == {"id": "dataset"}
    assert meta["languages"] == [{"id": "eng"}]
    assert meta["creators"] == RECORD["metadata"]["creators"]
