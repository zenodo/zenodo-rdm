# SPDX-FileCopyrightText: 2026 CERN
# SPDX-License-Identifier: GPL-3.0-or-later

"""Command-line entry point: ``zenodo-mcp`` or ``python -m zenodo_mcp``."""

import argparse

from .server import create_server


def main() -> None:
    """Run the server over stdio (default) or streamable HTTP."""
    parser = argparse.ArgumentParser(prog="zenodo-mcp", description=__doc__)
    parser.add_argument(
        "--transport", choices=("stdio", "streamable-http"), default="stdio"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = create_server()
    if args.transport == "stdio":
        server.run("stdio")
    else:
        server.run(
            "streamable-http",
            host=args.host,
            port=args.port,
            stateless_http=True,
            json_response=True,
        )


if __name__ == "__main__":
    main()
