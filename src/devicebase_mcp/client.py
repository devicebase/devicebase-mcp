"""Devicebase API client."""

from __future__ import annotations

from typing import Any

import httpx


class DevicebaseClient:
    """Client for Devicebase API."""

    def __init__(
        self, api_key: str | None = None, base_url: str = "https://api.devicebase.cn"
    ) -> None:
        """Initialize client."""
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def set_api_key(self, api_key: str) -> None:
        """Update the API key and headers."""
        self.api_key = api_key
        self._client.headers["Authorization"] = f"Bearer {api_key}"

    def _get_auth_header(self, context: Any = None) -> str | None:
        """Get Authorization header from context if available."""
        if context and hasattr(context, "request"):
            request = context.request
            if hasattr(request, "headers"):
                return request.headers.get("Authorization")
        return None

    def _request(
        self, method: str, path: str, context: Any = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make API request."""
        url = f"{self.base_url}/v1{path}"
        response = self._client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def _request_bytes(
        self, method: str, path: str, **kwargs: Any
    ) -> bytes:
        """Make API request and return raw response bytes."""
        url = f"{self.base_url}/v1{path}"
        response = self._client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.content

    def list_devices(
        self,
        keyword: str | None = None,
        state: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """List available devices."""
        params: dict[str, Any] = {"limit": limit}
        if keyword:
            params["keyword"] = keyword
        if state:
            params["state"] = state

        return self._request("GET", "/devices", params=params)

    def tap(self, serial: str, x: int, y: int) -> dict[str, Any]:
        """Tap at coordinates."""
        return self._request("POST", f"/tap/{serial}", json={"x": x, "y": y})

    def double_tap(self, serial: str, x: int, y: int) -> dict[str, Any]:
        """Double tap at coordinates."""
        return self._request("POST", f"/double_tap/{serial}", json={"x": x, "y": y})

    def long_press(self, serial: str, x: int, y: int, duration: int = 1000) -> dict[str, Any]:
        """Long press at coordinates."""
        return self._request("POST", f"/long_press/{serial}", json={"x": x, "y": y, "duration": duration})

    def swipe(self, serial: str, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> dict[str, Any]:
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
        )

    def back(self, serial: str) -> dict[str, Any]:
        """Press back button."""
        return self._request("POST", f"/back/{serial}")

    def home(self, serial: str) -> dict[str, Any]:
        """Press home button."""
        return self._request("POST", f"/home/{serial}")

    def launch_app(self, serial: str, package: str) -> dict[str, Any]:
        """Launch an application."""
        return self._request("POST", f"/launch_app/{serial}", json={"package": package})

    def current_app(self, serial: str) -> dict[str, Any]:
        """Get current foreground app."""
        return self._request("POST", f"/current_app/{serial}")

    def input_text(self, serial: str, text: str) -> dict[str, Any]:
        """Input text."""
        return self._request("POST", f"/input/{serial}", json={"text": text})

    def clear_text(self, serial: str) -> dict[str, Any]:
        """Clear text field."""
        return self._request("POST", f"/clear_text/{serial}")

    def device_info(self, serial: str) -> dict[str, Any]:
        """Get device information."""
        return self._request("POST", f"/deviceinfo/{serial}")

    def dump_hierarchy(self, serial: str) -> dict[str, Any]:
        """Get UI hierarchy."""
        return self._request("POST", f"/dump_hierarchy/{serial}")

    def screenshot(self, serial: str) -> str:
        """Get screenshot as base64-encoded image."""
        import base64

        data = self._request_bytes("GET", f"/screen/{serial}")
        return base64.b64encode(data).decode("ascii")
