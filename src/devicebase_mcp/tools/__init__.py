"""Devicebase MCP tools."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient


def register_all_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register all MCP tools."""
    from devicebase_mcp.tools.app import register_app_tools
    from devicebase_mcp.tools.device import register_device_tools
    from devicebase_mcp.tools.navigation import register_navigation_tools
    from devicebase_mcp.tools.text import register_text_tools
    from devicebase_mcp.tools.touch import register_touch_tools
    from devicebase_mcp.tools.ui import register_ui_tools

    register_device_tools(mcp, client)
    register_touch_tools(mcp, client)
    register_navigation_tools(mcp, client)
    register_app_tools(mcp, client)
    register_text_tools(mcp, client)
    register_ui_tools(mcp, client)
