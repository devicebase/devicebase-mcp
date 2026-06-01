"""Navigation tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient


def register_navigation_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register navigation tools."""

    @mcp.tool()
    def press_back(serial: str, ctx: Context | None = None) -> str:
        """Press the back button.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        result = client.back(serial, context=ctx)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def press_home(serial: str, ctx: Context | None = None) -> str:
        """Press the home button.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        result = client.home(serial, context=ctx)
        return json.dumps(result, ensure_ascii=False)
