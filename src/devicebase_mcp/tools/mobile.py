"""Mobile platform tools — Android / HarmonyOS / iOS.

Every tool targets ``/v1/{action}/{serialno}``. Coordinates are device pixels:
points are (x, y) and swipes take a start and an end point.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import ToolContext


def register_mobile_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register the mobile platform tools."""

    # --- Touch ---

    @mcp.tool()
    def mobile_tap(serialno: str, x: int, y: int, ctx: ToolContext | None = None) -> str:
        """Tap once at the given screen coordinates.

        Args:
            serialno: The mobile device serialno, from list_devices. Mobile
                serials come from list_devices(type="mobile").
            x: X coordinate in device pixels.
            y: Y coordinate in device pixels.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_tap(serialno, x, y, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_double_tap(serialno: str, x: int, y: int, ctx: ToolContext | None = None) -> str:
        """Double tap at the given screen coordinates.

        Args:
            serialno: The mobile device serialno, from list_devices.
            x: X coordinate in device pixels.
            y: Y coordinate in device pixels.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_double_tap(serialno, x, y, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_long_press(serialno: str, x: int, y: int, ctx: ToolContext | None = None) -> str:
        """Press and hold at the given screen coordinates.

        Args:
            serialno: The mobile device serialno, from list_devices.
            x: X coordinate in device pixels.
            y: Y coordinate in device pixels.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_long_press(serialno, x, y, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_swipe(
        serialno: str, x1: int, y1: int, x2: int, y2: int, ctx: ToolContext | None = None
    ) -> str:
        """Swipe from one point to another.

        Args:
            serialno: The mobile device serialno, from list_devices.
            x1: Start X coordinate in device pixels.
            y1: Start Y coordinate in device pixels.
            x2: End X coordinate in device pixels.
            y2: End Y coordinate in device pixels.

        Returns:
            JSON response from the API.
        """
        return json.dumps(
            client.mobile_swipe(serialno, x1, y1, x2, y2, context=ctx), ensure_ascii=False
        )

    # --- Navigation ---

    @mcp.tool()
    def mobile_back(serialno: str, ctx: ToolContext | None = None) -> str:
        """Press the device back button.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_back(serialno, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_home(serialno: str, ctx: ToolContext | None = None) -> str:
        """Press the device home button.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_home(serialno, context=ctx), ensure_ascii=False)

    # --- Apps and shell ---

    @mcp.tool()
    def mobile_launch_app(serialno: str, app_name: str, ctx: ToolContext | None = None) -> str:
        """Launch an app on the device.

        Args:
            serialno: The mobile device serialno, from list_devices.
            app_name: Package name (Android/HarmonyOS) or bundle ID (iOS).

        Returns:
            JSON response from the API.
        """
        return json.dumps(
            client.mobile_launch_app(serialno, app_name, context=ctx), ensure_ascii=False
        )

    @mcp.tool()
    def mobile_stop_app(serialno: str, app_name: str, ctx: ToolContext | None = None) -> str:
        """Stop an app on the device.

        Args:
            serialno: The mobile device serialno, from list_devices.
            app_name: Package name (Android/HarmonyOS) or bundle ID (iOS).

        Returns:
            JSON response from the API.
        """
        return json.dumps(
            client.mobile_stop_app(serialno, app_name, context=ctx), ensure_ascii=False
        )

    @mcp.tool()
    def mobile_stop_current_app(serialno: str, ctx: ToolContext | None = None) -> str:
        """Stop the app currently in the foreground.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_stop_current_app(serialno, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_current_app(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get the app currently in the foreground.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries app_name and package_name.
        """
        return json.dumps(client.mobile_current_app(serialno, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_bash(serialno: str, command: str, ctx: ToolContext | None = None) -> str:
        """Run a shell command on the device (adb/hdc platforms only).

        A non-zero command exit is reported in data.exitCode, not as a tool
        error — the API call itself succeeded.

        Args:
            serialno: The mobile device serialno, from list_devices.
            command: The shell command to run.

        Returns:
            JSON envelope whose data carries exitCode, stdout and stderr.
        """
        return json.dumps(client.mobile_bash(serialno, command, context=ctx), ensure_ascii=False)

    # --- Text ---

    @mcp.tool()
    def mobile_input_text(serialno: str, text: str, ctx: ToolContext | None = None) -> str:
        """Type text into the focused field.

        The device must already have a text field focused; tap it first.

        Args:
            serialno: The mobile device serialno, from list_devices.
            text: The text to type.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_input_text(serialno, text, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_clear_text(serialno: str, ctx: ToolContext | None = None) -> str:
        """Clear the focused text field.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON response from the API.
        """
        return json.dumps(client.mobile_clear_text(serialno, context=ctx), ensure_ascii=False)

    # --- State ---

    @mcp.tool()
    def mobile_device_info(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get device information: status, hardware, OS version, screen size.

        Use this to learn the screen resolution before converting coordinates
        returned by a vision model.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries the device detail.
        """
        return json.dumps(client.mobile_device_info(serialno, context=ctx), ensure_ascii=False)

    @mcp.tool()
    def mobile_dump_hierarchy(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get the UI element tree, for finding coordinates instead of guessing.

        Args:
            serialno: The mobile device serialno, from list_devices.

        Returns:
            JSON envelope whose data.hierarchy holds the tree.
        """
        return json.dumps(client.mobile_dump_hierarchy(serialno, context=ctx), ensure_ascii=False)

    # --- Install ---

    @mcp.tool()
    def mobile_install_app(serialno: str, app_path: str, ctx: ToolContext | None = None) -> str:
        """Install a package on the device.

        The path is resolved on the agent host that owns the device, not
        locally. The install runs as a background task: poll it with
        mobile_install_status.

        Args:
            serialno: The mobile device serialno, from list_devices.
            app_path: Package path on the agent host, e.g. /tmp/app.apk.

        Returns:
            JSON envelope whose data carries the install id.
        """
        return json.dumps(
            client.mobile_install_app(serialno, app_path, context=ctx), ensure_ascii=False
        )

    @mcp.tool()
    def mobile_install_status(
        serialno: str, install_id: str, ctx: ToolContext | None = None
    ) -> str:
        """Query a background install task started by mobile_install_app.

        Args:
            serialno: The mobile device serialno, from list_devices.
            install_id: The install id returned by mobile_install_app.

        Returns:
            JSON envelope describing the install.
        """
        return json.dumps(
            client.mobile_install_status(serialno, install_id, context=ctx),
            ensure_ascii=False,
        )
