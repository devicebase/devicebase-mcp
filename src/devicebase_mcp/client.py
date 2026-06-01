"""Devicebase API client."""

from __future__ import annotations

import re
from typing import Any

import httpx

_BEARER_RE = re.compile(r"^Bearer\s+(.+)$", re.IGNORECASE)


class DevicebaseClient:
    """Client for Devicebase API.

    Authentication precedence (per request):
        1. ``Authorization`` header carried on the incoming MCP request (highest).
        2. ``api_key`` configured at construction time (typically from
           ``DEVICEBASE_API_KEY``).
    """

    def __init__(
        self, api_key: str | None = None, base_url: str = "https://api.devicebase.cn"
    ) -> None:
        """Initialize client.

        Args:
            api_key: Fallback API key used when the incoming request does not
                carry its own ``Authorization`` header. Typically populated from
                the ``DEVICEBASE_API_KEY`` environment variable.
            base_url: Devicebase API base URL.
        """
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        # Default headers carry the fallback key. Per-request keys override
        # these on each call (see _request).
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    @staticmethod
    def _extract_bearer(auth_header: str | None) -> str | None:
        """Return the token from a ``Bearer <token>`` header, or ``None``."""
        if not auth_header:
            return None
        match = _BEARER_RE.match(auth_header.strip())
        return match.group(1) if match else None

    def _resolve_auth_header(self, context: Any = None) -> str:
        """Resolve the ``Authorization`` value for an outgoing request.

        Prefers the per-request header carried on the MCP ``Context``; falls
        back to the ``api_key`` provided at client construction.

        The MCP SDK chain is::

            FastMCP Context
              → .request_context  (mcp.shared.context.RequestContext)
                → .request         (starlette.requests.Request)
                  → .headers       (starlette.datastructures.Headers)
        """
        # 1. Per-request header from MCP context.
        request_auth: str | None = None
        request_context = getattr(context, "request_context", None)
        if request_context is not None:
            # RequestContext.request holds the original Starlette Request.
            starlette_request = getattr(request_context, "request", None)
            if starlette_request is not None:
                headers = getattr(starlette_request, "headers", None)
                if headers is not None:
                    # Starlette Headers supports dict-like .get.
                    try:
                        request_auth = headers.get("Authorization")
                    except AttributeError:
                        request_auth = None

        token = self._extract_bearer(request_auth)
        if token:
            return f"Bearer {token}"

        # 2. Fallback to env-derived key.
        return f"Bearer {self.api_key}"

    def _request(
        self, method: str, path: str, context: Any = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make API request.

        ``headers`` passed via ``kwargs`` are merged on top of the client's
        default headers, so callers can override ``Authorization`` per call.
        """
        url = f"{self.base_url}/v1{path}"
        merged_headers = {
            "Authorization": self._resolve_auth_header(context),
        }
        user_headers = kwargs.pop("headers", None) or {}
        merged_headers.update(user_headers)
        response = self._client.request(
            method, url, headers=merged_headers, **kwargs
        )
        response.raise_for_status()
        return response.json()

    def _request_bytes(
        self, method: str, path: str, context: Any = None, **kwargs: Any
    ) -> bytes:
        """Make API request and return raw response bytes."""
        url = f"{self.base_url}/v1{path}"
        merged_headers = {
            "Authorization": self._resolve_auth_header(context),
        }
        user_headers = kwargs.pop("headers", None) or {}
        merged_headers.update(user_headers)
        response = self._client.request(
            method, url, headers=merged_headers, **kwargs
        )
        response.raise_for_status()
        return response.content

    def list_devices(
        self,
        keyword: str | None = None,
        state: str | None = None,
        limit: int = 10,
        context: Any = None,
    ) -> dict[str, Any]:
        """List available devices."""
        params: dict[str, Any] = {"limit": limit}
        if keyword:
            params["keyword"] = keyword
        if state:
            params["state"] = state

        return self._request("GET", "/devices", params=params, context=context)

    def tap(
        self, serial: str, x: int, y: int, context: Any = None
    ) -> dict[str, Any]:
        """Tap at coordinates."""
        return self._request(
            "POST", f"/tap/{serial}", json={"x": x, "y": y}, context=context
        )

    def double_tap(
        self, serial: str, x: int, y: int, context: Any = None
    ) -> dict[str, Any]:
        """Double tap at coordinates."""
        return self._request(
            "POST", f"/double_tap/{serial}", json={"x": x, "y": y}, context=context
        )

    def long_press(
        self,
        serial: str,
        x: int,
        y: int,
        duration: int = 1000,
        context: Any = None,
    ) -> dict[str, Any]:
        """Long press at coordinates."""
        return self._request(
            "POST",
            f"/long_press/{serial}",
            json={"x": x, "y": y, "duration": duration},
            context=context,
        )

    def swipe(
        self,
        serial: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: int = 500,
        context: Any = None,
    ) -> dict[str, Any]:
        """Swipe from one point to another."""
        return self._request(
            "POST",
            f"/swipe/{serial}",
            json={
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "duration": duration,
            },
            context=context,
        )

    def back(self, serial: str, context: Any = None) -> dict[str, Any]:
        """Press back button."""
        return self._request("POST", f"/back/{serial}", context=context)

    def home(self, serial: str, context: Any = None) -> dict[str, Any]:
        """Press home button."""
        return self._request("POST", f"/home/{serial}", context=context)

    def launch_app(
        self, serial: str, package: str, context: Any = None
    ) -> dict[str, Any]:
        """Launch an application."""
        return self._request(
            "POST",
            f"/launch_app/{serial}",
            json={"package": package},
            context=context,
        )

    def current_app(self, serial: str, context: Any = None) -> dict[str, Any]:
        """Get current foreground app."""
        return self._request("POST", f"/current_app/{serial}", context=context)

    def input_text(
        self, serial: str, text: str, context: Any = None
    ) -> dict[str, Any]:
        """Input text."""
        return self._request(
            "POST", f"/input/{serial}", json={"text": text}, context=context
        )

    def clear_text(self, serial: str, context: Any = None) -> dict[str, Any]:
        """Clear text field."""
        return self._request("POST", f"/clear_text/{serial}", context=context)

    def device_info(self, serial: str, context: Any = None) -> dict[str, Any]:
        """Get device information."""
        return self._request("POST", f"/deviceinfo/{serial}", context=context)

    def dump_hierarchy(self, serial: str, context: Any = None) -> dict[str, Any]:
        """Get UI hierarchy."""
        return self._request("POST", f"/dump_hierarchy/{serial}", context=context)

    def screenshot(self, serial: str, context: Any = None) -> str:
        """Get screenshot as base64-encoded image."""
        import base64

        data = self._request_bytes("GET", f"/screen/{serial}", context=context)
        return base64.b64encode(data).decode("ascii")
