"""Device discovery and cross-family tools.

Neither of these belongs to a platform family: ``list_devices`` is how a
serialno is found, and ``screenshot`` is served by the same route for every
platform.
"""

from __future__ import annotations

import base64
import json

from mcp.server.fastmcp import FastMCP

from devicebase_mcp.client import DevicebaseClient
from devicebase_mcp.tools import ToolContext


def describe_image_format(data: bytes) -> str:
    """Sniff the image container from the leading bytes."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def register_device_tools(mcp: FastMCP, client: DevicebaseClient) -> None:
    """Register device discovery and cross-family tools."""

    @mcp.tool()
    def list_devices(
        keyword: str | None = None,
        state: str | None = None,
        type: str | None = None,
        limit: int = 10,
        ctx: ToolContext | None = None,
    ) -> str:
        """List the devices accessible to the current API key.

        Start here: this is how you find the `serialno` that every other tool
        needs, and a serialno is only meaningful within one platform family.

        Args:
            keyword: Case-insensitive substring match across name, alias_name,
                brand, model, serialno, device_sn, type, os_type, os_version,
                location and operator.
            state: Filter by device state: busy, free, or offline.
            type: Filter by category ("mobile", "browser", "computer") or by
                system type ("android", "harmonyos", "ios", "macos", "windows",
                "linux", "chrome", "chromium", "edge", "other"). System types
                match the device's os_type, because a device row only carries
                the coarse type — a Chrome browser is type=browser with
                os_type=Chrome.
            limit: Maximum number of devices to return (default 10).

        Returns:
            JSON envelope whose data array holds the device rows. Each row
            carries serialno (the platform key), device_sn, type, os_type,
            state and name.
        """
        result = client.list_devices(
            keyword=keyword, state=state, device_type=type, limit=limit, context=ctx
        )
        return json.dumps(result, ensure_ascii=False)

    @mcp.tool()
    def screenshot(serialno: str, ctx: ToolContext | None = None) -> str:
        """Capture a screenshot of a device, as a base64-encoded image.

        Works for any platform: the server dispatches the request by device
        type — computer gives a full-desktop capture, browser a CDP capture,
        otherwise the device image queue.

        Args:
            serialno: The device serialno, from list_devices.

        Returns:
            JSON with `image_format` (the server's format, JPEG) and
            `image_base64` holding the encoded image bytes.
        """
        data = client.screenshot_bytes(serialno, context=ctx)
        return json.dumps(
            {
                "image_format": describe_image_format(data),
                "image_base64": base64.b64encode(data).decode("ascii"),
            },
            ensure_ascii=False,
        )
