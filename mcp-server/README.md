# Zenodo MCP server

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that
lets AI assistants search, read and deposit to Zenodo through its public REST
API. It runs on the user's own machine, talks to `https://zenodo.org/api` (or
any InvenioRDM instance), and needs no changes to the Zenodo deployment.

## Tools

Read-only (no token needed):

| Tool | What it does |
| --- | --- |
| `zenodo_search_records` | Search published records, with filters for resource type and community |
| `zenodo_get_record` | Metadata, DOIs, license and stats for one record (id, DOI or URL) |
| `zenodo_list_versions` | Every published version of a record |
| `zenodo_list_files` | File names, sizes, checksums and download URLs |
| `zenodo_search_communities` | Search communities |
| `zenodo_get_community` | One community's details |
| `zenodo_search_vocabulary` | Look up ids for licenses, resource types, languages, affiliations, funders and awards |
| `zenodo_list_my_records` | Your records and drafts (shown only when a token is set) |

Depositing (shown only when `ZENODO_TOKEN` is set and `ZENODO_READ_ONLY` is not):

| Tool | What it does |
| --- | --- |
| `zenodo_create_draft` | Create an unpublished draft |
| `zenodo_update_draft` | Change a draft's metadata, or open an edit of a published record |
| `zenodo_upload_file` | Upload a local file to a draft |
| `zenodo_delete_draft_file` | Remove a file from a draft |
| `zenodo_publish_draft` | Publish (mints a DOI), or submit to a community for review |
| `zenodo_new_version` | Start a new version of a published record |
| `zenodo_discard_draft` | Throw away a draft or pending edits |

Publishing cannot be undone. The tool is marked destructive and the server
instructions tell the model to get the user's explicit go-ahead first.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `ZENODO_BASE_URL` | `https://zenodo.org` | Use `https://sandbox.zenodo.org` while trying things out |
| `ZENODO_TOKEN` | unset | Personal access token from *Account → Applications*. Scopes: `deposit:write`, plus `deposit:actions` to publish |
| `ZENODO_READ_ONLY` | unset | Set to `1` to hide the deposit tools even when a token is set |
| `ZENODO_TIMEOUT` | `60` | HTTP timeout in seconds |
| `ZENODO_UPLOAD_DIR` | unset | If set, `zenodo_upload_file` only reads files inside this folder |

## Install and run

```bash
cd mcp-server
pip install .
zenodo-mcp            # stdio, for desktop clients
zenodo-mcp --transport streamable-http --port 8000
```

Example client entry (Claude Desktop, Claude Code, and other MCP clients use
the same shape):

```json
{
  "mcpServers": {
    "zenodo": {
      "command": "zenodo-mcp",
      "env": {
        "ZENODO_BASE_URL": "https://sandbox.zenodo.org",
        "ZENODO_TOKEN": "<your sandbox token>"
      }
    }
  }
}
```

## Security notes

- The token is read from the environment, sent only to `ZENODO_BASE_URL`, and
  never included in tool output.
- `zenodo_upload_file` reads a local path chosen by the model. Set
  `ZENODO_UPLOAD_DIR` to confine it to one folder, run the server
  as a user that can only read files you are willing to upload, or set
  `ZENODO_READ_ONLY=1`.
- The HTTP transport binds to `127.0.0.1` by default and has no
  authentication of its own; do not expose it on a public interface with a
  token configured.

## Tests

```bash
pip install ".[tests]"
./run-tests.sh
```

The tests stub the network with `httpx.MockTransport`, so they run offline.
