"""Devicebase MCP Server."""

import os

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import register_all_tools


def main() -> None:
    """Run the MCP server."""
    base_url = os.environ.get("DEVICEBASE_BASE_URL", "https://api.devicebase.cn")
    host = os.environ.get("MCP_HOST", "localhost")
    port = int(os.environ.get("MCP_PORT", "8080"))

    mcp = FastMCP(
        "Devicebase",
        json_response=True,
        host=host,
        port=port,
    )

    # Create client with environment variable (optional, headers take precedence)
    env_api_key = os.environ.get("DEVICEBASE_API_KEY")
    client = DevicebaseClient(api_key=env_api_key, base_url=base_url)

    register_all_tools(mcp, client)

    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
