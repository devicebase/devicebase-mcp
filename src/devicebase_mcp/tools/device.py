"""Device management tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient


def register_device_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register device management tools."""

    @mcp.tool()
    def list_devices(
        keyword: str | None = None,
        state: str | None = None,
        limit: int = 10,
        ctx: Context | None = None,
    ) -> str:
        """List available devices.

        Args:
            keyword: Filter by brand, model, serial, or name.
            state: Filter by device state: busy, free, or offline.
            limit: Maximum number of devices to return (default 10).

        Returns:
            JSON response from the API.
        """
        result = client.list_devices(
            keyword=keyword, state=state, limit=limit, context=ctx
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def get_device_info(serial: str, ctx: Context | None = None) -> str:
        """Get detailed information about a specific device.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        result = client.device_info(serial, context=ctx)
        return json.dumps(result, ensure_ascii=False)
