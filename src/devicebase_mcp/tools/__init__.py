"""Devicebase MCP tools.

Tool names are prefixed by platform (``mobile_``, ``browser_``, ``computer_``)
so a flat tool list stays unambiguous — the three platforms each have a "click"
or a "screenshot". The two platform-agnostic tools, ``list_devices`` and
``screenshot``, are deliberately unprefixed.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from devicebase_mcp.client import DevicebaseClient

#: The MCP tool context, with Context's three type parameters left open.
#: A bare `Context` is a mypy --strict error.
ToolContext = Context[Any, Any, Any]


def register_all_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register every MCP tool."""
    from devicebase_mcp.tools.browser import register_browser_tools
    from devicebase_mcp.tools.computer import register_computer_tools
    from devicebase_mcp.tools.device import register_device_tools
    from devicebase_mcp.tools.mobile import register_mobile_tools

    # Discovery first: every other tool depends on the serialno it returns.
    register_device_tools(mcp, client)
    register_mobile_tools(mcp, client)
    register_browser_tools(mcp, client)
    register_computer_tools(mcp, client)
