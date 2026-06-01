"""Touch interaction tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient


def register_touch_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register touch interaction tools."""

    @mcp.tool()
    def tap(serial: str, x: int, y: int, ctx: Context | None = None) -> str:
        """Perform a single tap at the specified coordinates.

        Args:
            serial: The device serial number.
            x: X coordinate (horizontal position).
            y: Y coordinate (vertical position).

        Returns:
            JSON response from the API.
        """
        result = client.tap(serial, x, y, context=ctx)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def double_tap(serial: str, x: int, y: int, ctx: Context | None = None) -> str:
        """Perform a double tap at the specified coordinates.

        Args:
            serial: The device serial number.
            x: X coordinate (horizontal position).
            y: Y coordinate (vertical position).

        Returns:
            JSON response from the API.
        """
        result = client.double_tap(serial, x, y, context=ctx)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def long_press(
        serial: str, x: int, y: int, duration: int = 1000, ctx: Context | None = None
    ) -> str:
        """Perform a long press at the specified coordinates.

        Args:
            serial: The device serial number.
            x: X coordinate (horizontal position).
            y: Y coordinate (vertical position).
            duration: Press duration in milliseconds (default 1000).

        Returns:
            JSON response from the API.
        """
        result = client.long_press(serial, x, y, duration, context=ctx)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def swipe(
        serial: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: int = 500,
        ctx: Context | None = None,
    ) -> str:
        """Perform a swipe gesture from one point to another.

        Args:
            serial: The device serial number.
            x1: Start X coordinate.
            y1: Start Y coordinate.
            x2: End X coordinate.
            y2: End Y coordinate.
            duration: Swipe duration in milliseconds (default 500).

        Returns:
            JSON response from the API.
        """
        result = client.swipe(serial, x1, y1, x2, y2, duration, context=ctx)
        return json.dumps(result, ensure_ascii=False)
