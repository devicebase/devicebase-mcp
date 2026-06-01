"""App management tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient


def register_app_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register app management tools."""

    @mcp.tool()
    def launch_app(serial: str, package: str, ctx: Context | None = None) -> str:
        """Launch an application on the device.

        Args:
            serial: The device serial number.
            package: The app package name (Android) or bundle ID (iOS).
                     Examples: com.android.settings, com.apple.Maps

        Returns:
            JSON response from the API.
        """
        result = client.launch_app(serial, package, context=ctx)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def get_current_app(serial: str, ctx: Context | None = None) -> str:
        """Get the currently foreground application.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        result = client.current_app(serial, context=ctx)
        return json.dumps(result, ensure_ascii=False)
