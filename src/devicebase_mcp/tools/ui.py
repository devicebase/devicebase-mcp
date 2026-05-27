"""UI inspection tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools.device import extract_api_key


def register_ui_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register UI inspection tools."""

    @mcp.tool()
    def dump_hierarchy(serial: str, ctx: Context | None = None) -> str:
        """Get the UI element hierarchy/tree.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        if ctx:
            extract_api_key(client, ctx)
        hierarchy = client.dump_hierarchy(serial)
        return json.dumps(hierarchy, ensure_ascii=False)

    @mcp.tool()
    def screenshot(serial: str, ctx: Context | None = None) -> str:
        """Capture the device screen.

        Args:
            serial: The device serial number.

        Returns:
            Base64-encoded PNG image of the current screen.
        """
        if ctx:
            extract_api_key(client, ctx)
        image = client.screenshot(serial)
        return image
