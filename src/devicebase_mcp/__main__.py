"""Devicebase MCP Server.

Two transports are supported:

* **stdio** (default) — for MCP clients that launch the server as a
  subprocess, such as Claude Code and VS Code. There is no incoming HTTP
  request, so the API key always comes from ``DEVICEBASE_API_KEY``.
* **streamable-http** — for clients that connect over HTTP. The API key is
  taken from the incoming request's ``Authorization`` header when present, and
  falls back to ``DEVICEBASE_API_KEY``.

Pick one with ``--transport`` or ``MCP_TRANSPORT``.
"""

from __future__ import annotations

import argparse
import os
from typing import Literal

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DEFAULT_BASE_URL, DevicebaseClient
from devicebase_mcp.tools import register_all_tools

Transport = Literal["stdio", "streamable-http"]

DEFAULT_TRANSPORT: Transport = "stdio"


def build_server(
    transport: Transport = DEFAULT_TRANSPORT,
    host: str = "localhost",
    port: int = 8080,
) -> FastMCP:
    """Build the MCP server with every Devicebase tool registered."""
    base_url = os.environ.get("DEVICEBASE_BASE_URL", DEFAULT_BASE_URL)

    mcp = FastMCP(
        "Devicebase",
        json_response=True,
        host=host,
        port=port,
    )

    # Seed the client with the env-var key. Over streamable-http, a per-request
    # ``Authorization`` header takes precedence; the env value is only used when
    # the request omits the header. Over stdio there is no request, so the env
    # value is the only source.
    client = DevicebaseClient(api_key=os.environ.get("DEVICEBASE_API_KEY"), base_url=base_url)

    register_all_tools(mcp, client)
    return mcp


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the server's command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="devicebase-mcp",
        description="MCP server for the Devicebase device automation API.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=os.environ.get("MCP_TRANSPORT", DEFAULT_TRANSPORT),
        help="Transport to serve on (default: stdio, or MCP_TRANSPORT).",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "localhost"),
        help="Bind host for streamable-http (default: localhost, or MCP_HOST).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8080")),
        help="Bind port for streamable-http (default: 8080, or MCP_PORT).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run the MCP server."""
    args = parse_args(argv)
    mcp = build_server(transport=args.transport, host=args.host, port=args.port)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
