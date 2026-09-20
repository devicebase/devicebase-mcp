"""Computer platform tools — macOS / Windows / Linux desktops.

Every tool targets ``/api/computer/{serialno}/{action}``. Coordinates are
absolute screen pixels. The serialno is a computer device's, from
``list_devices(type="computer")``.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import ToolContext


def register_computer_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register the computer platform tools."""

    def emit(result: dict[str, Any]) -> str:
        return json.dumps(result, ensure_ascii=False)

    # --- Mouse ---

    @mcp.tool()
    def computer_click(
        serialno: str, x: int, y: int, button: str | None = None, ctx: ToolContext | None = None
    ) -> str:
        """Click at absolute screen coordinates.

        Args:
            serialno: The computer device serialno, from list_devices.
            x: X coordinate in screen pixels.
            y: Y coordinate in screen pixels.
            button: "left", "right" or "middle". Omit it for the server default
                (left).

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_click(serialno, x, y, button=button, context=ctx))

    @mcp.tool()
    def computer_double_click(serialno: str, x: int, y: int, ctx: ToolContext | None = None) -> str:
        """Double click at absolute screen coordinates (left button).

        Args:
            serialno: The computer device serialno, from list_devices.
            x: X coordinate in screen pixels.
            y: Y coordinate in screen pixels.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_double_click(serialno, x, y, context=ctx))

    @mcp.tool()
    def computer_long_click(
        serialno: str, x: int, y: int, duration: int = 0, ctx: ToolContext | None = None
    ) -> str:
        """Press and hold the left button at the coordinates.

        Args:
            serialno: The computer device serialno, from list_devices.
            x: X coordinate in screen pixels.
            y: Y coordinate in screen pixels.
            duration: Hold duration in SECONDS. Omit or 0 for the driver
                default.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_long_click(serialno, x, y, duration, context=ctx))

    @mcp.tool()
    def computer_move(serialno: str, x: int, y: int, ctx: ToolContext | None = None) -> str:
        """Move the mouse without clicking.

        Args:
            serialno: The computer device serialno, from list_devices.
            x: X coordinate in screen pixels.
            y: Y coordinate in screen pixels.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_move(serialno, x, y, context=ctx))

    @mcp.tool()
    def computer_drag(
        serialno: str, x1: int, y1: int, x2: int, y2: int, ctx: ToolContext | None = None
    ) -> str:
        """Press the left button at one point, move to another, and release.

        Args:
            serialno: The computer device serialno, from list_devices.
            x1: Start X coordinate in screen pixels.
            y1: Start Y coordinate in screen pixels.
            x2: End X coordinate in screen pixels.
            y2: End Y coordinate in screen pixels.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_drag(serialno, x1, y1, x2, y2, context=ctx))

    @mcp.tool()
    def computer_scroll(
        serialno: str,
        direction: str,
        amount: int = 0,
        ctx: ToolContext | None = None,
    ) -> str:
        """Scroll the mouse wheel.

        Args:
            serialno: The computer device serialno, from list_devices.
            direction: One of "up", "down", "left", "right".
            amount: Wheel steps. Omit or 0 for the driver default.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_scroll(serialno, direction, amount, context=ctx))

    # --- Keyboard ---

    @mcp.tool()
    def computer_type_text(serialno: str, text: str, ctx: ToolContext | None = None) -> str:
        """Type text at the current caret of the focused app.

        Args:
            serialno: The computer device serialno, from list_devices.
            text: The text to type.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_type_text(serialno, text, context=ctx))

    @mcp.tool()
    def computer_press(serialno: str, key: str, ctx: ToolContext | None = None) -> str:
        """Press a single key.

        Args:
            serialno: The computer device serialno, from list_devices.
            key: The key name, e.g. Enter or F5.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_press(serialno, key, context=ctx))

    @mcp.tool()
    def computer_hotkey(serialno: str, keys: list[str], ctx: ToolContext | None = None) -> str:
        """Press keys together, e.g. ["Control", "Shift", "Escape"].

        Args:
            serialno: The computer device serialno, from list_devices.
            keys: The keys to press together.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_hotkey(serialno, keys, context=ctx))

    # --- System ---

    @mcp.tool()
    def computer_position(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get the current mouse position.

        Args:
            serialno: The computer device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries the position.
        """
        return emit(client.computer_position(serialno, context=ctx))

    @mcp.tool()
    def computer_screen_size(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get the primary screen size.

        Use this to convert coordinates returned by a vision model before
        calling computer_click.

        Args:
            serialno: The computer device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries the screen size.
        """
        return emit(client.computer_screen_size(serialno, context=ctx))

    @mcp.tool()
    def computer_permissions(serialno: str, ctx: ToolContext | None = None) -> str:
        """Get the desktop-control permission status.

        Args:
            serialno: The computer device serialno, from list_devices.

        Returns:
            JSON envelope whose data carries the permission status.
        """
        return emit(client.computer_permissions(serialno, context=ctx))

    @mcp.tool()
    def computer_launch_app(serialno: str, app_name: str, ctx: ToolContext | None = None) -> str:
        """Launch a desktop application.

        Args:
            serialno: The computer device serialno, from list_devices.
            app_name: The application name.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_launch_app(serialno, app_name, context=ctx))

    # --- Blocking actions ---

    @mcp.tool()
    def computer_wait(serialno: str, milliseconds: int, ctx: ToolContext | None = None) -> str:
        """Block for a duration, useful between steps in a script.

        Args:
            serialno: The computer device serialno, from list_devices.
            milliseconds: How long to block, in MILLISECONDS (1-300000). Note
                that computer_bash's timeout is in seconds.

        Returns:
            JSON response from the API.
        """
        return emit(client.computer_wait(serialno, milliseconds, context=ctx))

    @mcp.tool()
    def computer_bash(
        serialno: str, command: str, timeout: int = 0, ctx: ToolContext | None = None
    ) -> str:
        """Run a shell command on the host machine that owns this device.

        Danger tier: the command runs as the desktop user, unsandboxed, under
        the platform default shell (/bin/sh on macOS/Linux, cmd.exe on
        Windows), so bash-only syntax such as [[ ]] may not work. Treat it as
        shell access.

        A non-zero command exit is reported in data.exitCode, not as a tool
        error — the API call itself succeeded.

        Args:
            serialno: The computer device serialno, from list_devices.
            command: The shell command to run.
            timeout: Command budget in SECONDS. Omit or 0 to let the server
                apply its 120s default.

        Returns:
            JSON envelope whose data carries exitCode, stdout and stderr.
        """
        return emit(client.computer_bash(serialno, command, timeout, context=ctx))
