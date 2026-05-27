"""Device management tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient


def extract_api_key(client: DevicebaseClient, ctx: Context) -> None:
    """Extract API key from request headers if present."""
    if ctx.request_context and hasattr(ctx.request_context, "headers"):
        auth_header = ctx.request_context.headers.get("Authorization")
        if auth_header:
            import re

            match = re.match(r"Bearer\s+(.+)", auth_header, re.IGNORECASE)
            if match:
                client.set_api_key(match.group(1))


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
        if ctx:
            extract_api_key(client, ctx)
        result = client.list_devices(keyword=keyword, state=state, limit=limit)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def get_device_info(serial: str, ctx: Context | None = None) -> str:
        """Get detailed information about a specific device.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        if ctx:
            extract_api_key(client, ctx)
        result = client.device_info(serial)
        return json.dumps(result, ensure_ascii=False)
