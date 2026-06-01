"""Text input tools."""

from __future__ import annotations

import json

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient


def register_text_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register text input tools."""

    @mcp.tool()
    def input_text(serial: str, text: str, ctx: Context | None = None) -> str:
        """Input text into the currently focused text field.

        Args:
            serial: The device serial number.
            text: The text to input.

        Returns:
            JSON response from the API.
        """
        result = client.input_text(serial, text, context=ctx)
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def clear_text(serial: str, ctx: Context | None = None) -> str:
        """Clear text from the currently focused text field.

        Args:
            serial: The device serial number.

        Returns:
            JSON response from the API.
        """
        result = client.clear_text(serial, context=ctx)
        return json.dumps(result, ensure_ascii=False)
