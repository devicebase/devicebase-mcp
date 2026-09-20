"""Devicebase API client.

Three device platforms are covered, each with its own path family:

* **mobile** (Android / HarmonyOS / iOS) — ``/v1/{action}/{serialno}``
* **browser** (Chrome / Chromium / Edge over CDP) —
  ``/api/browser/{serialno}/{action...}``
* **computer** (macOS / Windows / Linux desktops) —
  ``/api/computer/{serialno}/{action}``

The serialno of a device is discovered with :meth:`DevicebaseClient.list_devices`
and is only meaningful within one platform family.
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any
from urllib.parse import quote

import httpx

from .errors import (
    AuthenticationError,
    BusinessError,
    DevicebaseError,
    DeviceNotFoundError,
    ValidationError,
)

_BEARER_RE = re.compile(r"^Bearer\s+(.+)$", re.IGNORECASE)

DEFAULT_BASE_URL = "https://api.devicebase.cn"

#: Deadline for an ordinary request, in seconds.
DEFAULT_TIMEOUT = 30.0

#: Headroom added on top of a blocking action's own budget, covering connect
#: and body-read overhead.
ACTION_TIMEOUT_MARGIN = 15.0

#: The server's own default for a computer bash command, in seconds. Used only
#: to size the client deadline when the caller omits a timeout.
DEFAULT_BASH_TIMEOUT_SECONDS = 120

#: Cap on the body text kept in an error message.
MAX_ERROR_BODY_CHARS = 4096


def _escape(serialno: str) -> str:
    """URL-quote a serialno so it cannot break out of a path segment."""
    return quote(str(serialno), safe="")


def mobile_path(serialno: str, action: str) -> str:
    """Build ``/v1/{action}/{serialno}`` — the mobile route family."""
    return f"/v1/{action}/{_escape(serialno)}"


def browser_path(serialno: str, action: str) -> str:
    """Build ``/api/browser/{serialno}/{action}``."""
    return f"/api/browser/{_escape(serialno)}/{action}"


def computer_path(serialno: str, action: str) -> str:
    """Build ``/api/computer/{serialno}/{action}``."""
    return f"/api/computer/{_escape(serialno)}/{action}"


def bash_timeout(timeout_seconds: int) -> float:
    """Bound the HTTP deadline for a bash call.

    It has to exceed the requested command timeout, or the client would abort a
    command the server is still running and report a transport error.
    """
    seconds = timeout_seconds if timeout_seconds > 0 else DEFAULT_BASH_TIMEOUT_SECONDS
    return seconds + ACTION_TIMEOUT_MARGIN


def wait_timeout(milliseconds: int) -> float:
    """The same idea for ``wait``, whose budget arrives as milliseconds."""
    return max(0, milliseconds) / 1000 + ACTION_TIMEOUT_MARGIN


def _truncate(body: str) -> str:
    if len(body) <= MAX_ERROR_BODY_CHARS:
        return body
    return body[:MAX_ERROR_BODY_CHARS] + "… (truncated)"


def _check_envelope(text: str) -> None:
    """Raise when the body carries a business error.

    The control API reports action failures in the response envelope — HTTP 200
    with a non-2xx ``code`` field, e.g. ``{"code":502,"message":"-32602: ..."}``
    when a browser action fails in the driver. Trusting the status line alone
    reports those as success.

    Bodies that are not an envelope (arrays, empty, non-JSON) are left alone, as
    are codes inside the 2xx range.
    """
    stripped = text.lstrip()
    if not stripped.startswith("{"):
        return
    try:
        parsed = json.loads(stripped)
    except ValueError:
        return
    if not isinstance(parsed, dict):
        return
    code = parsed.get("code")
    if not isinstance(code, int) or isinstance(code, bool):
        return
    if 200 <= code < 300:
        return
    raise BusinessError(code, text)


def _error_for_status(status: int, body: str) -> DevicebaseError:
    message = f"API error (HTTP {status}): {_truncate(body)}"
    if status == 401:
        return AuthenticationError(message)
    if status == 404:
        return DeviceNotFoundError(message)
    if status in (400, 422):
        # The gateway reports validation failures as 400; 422 is kept for
        # compatibility with older deployments.
        return ValidationError(message)
    return DevicebaseError(message)


class DevicebaseClient:
    """Client for the Devicebase API.

    Authentication precedence (per request):
        1. ``Authorization`` header carried on the incoming MCP request (highest).
        2. ``api_key`` configured at construction time (typically from
           ``DEVICEBASE_API_KEY``).
    """

    def __init__(self, api_key: str | None = None, base_url: str = DEFAULT_BASE_URL) -> None:
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
            timeout=DEFAULT_TIMEOUT,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

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

    def _send(
        self,
        method: str,
        path: str,
        context: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send a request and raise for either failure layer.

        ``headers`` passed via ``kwargs`` are merged on top of the client's
        default headers, so callers can override ``Authorization`` per call.
        ``timeout`` overrides the client-wide deadline for a blocking action.
        """
        if not self.api_key and self._resolve_auth_header(context) == "Bearer ":
            raise AuthenticationError(
                "API key is required: set DEVICEBASE_API_KEY or send an "
                "Authorization header with the request"
            )

        url = f"{self.base_url}{path}"
        merged_headers = {"Authorization": self._resolve_auth_header(context)}
        merged_headers.update(kwargs.pop("headers", None) or {})

        request_kwargs: dict[str, Any] = {"headers": merged_headers, **kwargs}
        if timeout is not None:
            request_kwargs["timeout"] = timeout

        response = self._client.request(method, url, **request_kwargs)

        if response.status_code >= 400:
            raise _error_for_status(response.status_code, response.text)
        _check_envelope(response.text)
        return response

    def _request(
        self,
        method: str,
        path: str,
        context: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request and decode the JSON envelope."""
        response = self._send(method, path, context, timeout, **kwargs)
        if not response.content:
            return {}
        try:
            decoded: dict[str, Any] = response.json()
        except ValueError as exc:
            raise DevicebaseError(f"invalid JSON response: {_truncate(response.text)}") from exc
        return decoded

    def _request_bytes(
        self,
        method: str,
        path: str,
        context: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> bytes:
        """Make an API request and return the raw response bytes."""
        return self._send(method, path, context, timeout, **kwargs).content

    # --- Devices ----------------------------------------------------------

    def list_devices(
        self,
        keyword: str | None = None,
        state: str | None = None,
        device_type: str | None = None,
        limit: int | None = 10,
        context: Any = None,
    ) -> dict[str, Any]:
        """List the devices accessible to the current API key.

        Filtering is resolved server-side. ``device_type`` accepts either a
        category bucket (mobile|browser|computer) or a system type
        (android|harmonyos|ios|macos|windows|linux|chrome|chromium|edge|other);
        buckets match against the device's os_type, because a device row only
        carries the coarse type.
        """
        params: dict[str, Any] = {}
        if keyword:
            params["keyword"] = keyword
        if state:
            params["state"] = state
        if device_type:
            params["type"] = device_type
        if limit:
            params["limit"] = limit

        result: dict[str, Any] = self._request("GET", "/v1/devices", context=context, params=params)
        return result

    # --- Mobile -----------------------------------------------------------

    def mobile_device_info(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get device information."""
        return self._request("POST", mobile_path(serialno, "deviceinfo"), context=context)

    def mobile_tap(self, serialno: str, x: int, y: int, context: Any = None) -> dict[str, Any]:
        """Tap at coordinates."""
        return self._request(
            "POST", mobile_path(serialno, "tap"), context=context, json={"x": x, "y": y}
        )

    def mobile_double_tap(
        self, serialno: str, x: int, y: int, context: Any = None
    ) -> dict[str, Any]:
        """Double tap at coordinates."""
        return self._request(
            "POST", mobile_path(serialno, "double_tap"), context=context, json={"x": x, "y": y}
        )

    def mobile_long_press(
        self, serialno: str, x: int, y: int, context: Any = None
    ) -> dict[str, Any]:
        """Long press at coordinates."""
        return self._request(
            "POST", mobile_path(serialno, "long_press"), context=context, json={"x": x, "y": y}
        )

    def mobile_swipe(
        self, serialno: str, x1: int, y1: int, x2: int, y2: int, context: Any = None
    ) -> dict[str, Any]:
        """Swipe from one point to another."""
        return self._request(
            "POST",
            mobile_path(serialno, "swipe"),
            context=context,
            json={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        )

    def mobile_back(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Press the back button."""
        return self._request("POST", mobile_path(serialno, "back"), context=context)

    def mobile_home(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Press the home button."""
        return self._request("POST", mobile_path(serialno, "home"), context=context)

    def mobile_launch_app(
        self, serialno: str, app_name: str, context: Any = None
    ) -> dict[str, Any]:
        """Launch an application."""
        return self._request(
            "POST",
            mobile_path(serialno, "launch_app"),
            context=context,
            json={"app_name": app_name},
        )

    def mobile_stop_app(self, serialno: str, app_name: str, context: Any = None) -> dict[str, Any]:
        """Stop an application."""
        return self._request(
            "POST",
            mobile_path(serialno, "stop_app"),
            context=context,
            json={"app_name": app_name},
        )

    def mobile_stop_current_app(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Stop the app currently in the foreground."""
        return self._request("POST", mobile_path(serialno, "stop_current_app"), context=context)

    def mobile_current_app(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get the current foreground app."""
        return self._request("POST", mobile_path(serialno, "current_app"), context=context)

    def mobile_input_text(self, serialno: str, text: str, context: Any = None) -> dict[str, Any]:
        """Type text into the focused field."""
        return self._request(
            "POST", mobile_path(serialno, "input"), context=context, json={"text": text}
        )

    def mobile_clear_text(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Clear the focused text field."""
        return self._request("POST", mobile_path(serialno, "clear_text"), context=context)

    def mobile_bash(self, serialno: str, command: str, context: Any = None) -> dict[str, Any]:
        """Run a shell command on the device (adb/hdc platforms only).

        The command's own exit status comes back in the payload as
        ``data.exitCode`` — a non-zero value is not an API error.
        """
        return self._request(
            "POST", mobile_path(serialno, "bash"), context=context, json={"command": command}
        )

    def mobile_dump_hierarchy(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get the UI hierarchy."""
        return self._request("POST", mobile_path(serialno, "dump_hierarchy"), context=context)

    def mobile_install_app(
        self, serialno: str, app_path: str, context: Any = None
    ) -> dict[str, Any]:
        """Install a package from a path on the agent host."""
        return self._request(
            "POST",
            mobile_path(serialno, "install_app"),
            context=context,
            json={"app_path": app_path},
        )

    def mobile_install_status(
        self, serialno: str, install_id: str, context: Any = None
    ) -> dict[str, Any]:
        """Query a background install task."""
        return self._request(
            "GET",
            mobile_path(serialno, "install_status"),
            context=context,
            params={"install_id": install_id},
        )

    # --- Browser ----------------------------------------------------------

    def browser_navigate(self, serialno: str, url: str, context: Any = None) -> dict[str, Any]:
        """Navigate the current tab to a URL."""
        return self._request(
            "POST", browser_path(serialno, "navigate"), context=context, json={"url": url}
        )

    def browser_refresh(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Reload the current page."""
        return self._request("POST", browser_path(serialno, "refresh"), context=context)

    def browser_go_back(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Navigate back in the browser history."""
        return self._request("POST", browser_path(serialno, "go_back"), context=context)

    def browser_go_forward(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Navigate forward in the browser history."""
        return self._request("POST", browser_path(serialno, "go_forward"), context=context)

    def browser_input(self, serialno: str, text: str, context: Any = None) -> dict[str, Any]:
        """Insert text into the focused element (CDP Input.insertText)."""
        return self._request(
            "POST", browser_path(serialno, "input"), context=context, json={"text": text}
        )

    def browser_click(self, serialno: str, selector: str, context: Any = None) -> dict[str, Any]:
        """Click the element matching a CSS selector."""
        return self._request(
            "POST", browser_path(serialno, "click"), context=context, json={"selector": selector}
        )

    def browser_fill(
        self, serialno: str, selector: str, value: str, context: Any = None
    ) -> dict[str, Any]:
        """Clear an input and type a value into it."""
        return self._request(
            "POST",
            browser_path(serialno, "fill"),
            context=context,
            json={"selector": selector, "value": value},
        )

    def browser_select(
        self, serialno: str, selector: str, value: str, context: Any = None
    ) -> dict[str, Any]:
        """Pick an option in a dropdown."""
        return self._request(
            "POST",
            browser_path(serialno, "select"),
            context=context,
            json={"selector": selector, "value": value},
        )

    def browser_text(self, serialno: str, selector: str, context: Any = None) -> dict[str, Any]:
        """Get an element's text content."""
        return self._request(
            "GET",
            browser_path(serialno, "text"),
            context=context,
            params={"selector": selector},
        )

    def browser_attribute(
        self, serialno: str, selector: str, attribute: str, context: Any = None
    ) -> dict[str, Any]:
        """Get one attribute of an element."""
        return self._request(
            "GET",
            browser_path(serialno, "attribute"),
            context=context,
            params={"selector": selector, "attribute": attribute},
        )

    def browser_exists(self, serialno: str, selector: str, context: Any = None) -> dict[str, Any]:
        """Report whether an element is present."""
        return self._request(
            "GET",
            browser_path(serialno, "exists"),
            context=context,
            params={"selector": selector},
        )

    def browser_execute(self, serialno: str, script: str, context: Any = None) -> dict[str, Any]:
        """Evaluate JavaScript in the page (danger tier)."""
        return self._request(
            "POST", browser_path(serialno, "execute"), context=context, json={"script": script}
        )

    def browser_hotkey(self, serialno: str, keys: list[str], context: Any = None) -> dict[str, Any]:
        """Press the given keys together."""
        return self._request(
            "POST", browser_path(serialno, "hotkey"), context=context, json={"keys": keys}
        )

    def browser_state(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get the current URL, title, viewport and tab count."""
        return self._request("GET", browser_path(serialno, "state"), context=context)

    def browser_tabs(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """List the open tabs."""
        return self._request("GET", browser_path(serialno, "tabs"), context=context)

    def browser_tab_open(self, serialno: str, url: str, context: Any = None) -> dict[str, Any]:
        """Open a new tab at a URL."""
        return self._request(
            "POST", browser_path(serialno, "tab/open"), context=context, json={"url": url}
        )

    def browser_tab_close(self, serialno: str, tab_id: str, context: Any = None) -> dict[str, Any]:
        """Close one tab."""
        return self._request(
            "POST", browser_path(serialno, "tab/close"), context=context, json={"tab_id": tab_id}
        )

    def browser_tab_close_all(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Close every tab."""
        return self._request("POST", browser_path(serialno, "tab/close_all"), context=context)

    def browser_tab_switch(self, serialno: str, tab_id: str, context: Any = None) -> dict[str, Any]:
        """Focus one tab."""
        return self._request(
            "POST", browser_path(serialno, "tab/switch"), context=context, json={"tab_id": tab_id}
        )

    def browser_launch(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Start the browser / CDP endpoint."""
        return self._request("POST", browser_path(serialno, "launch"), context=context)

    def browser_close(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Stop the browser / CDP endpoint."""
        return self._request("POST", browser_path(serialno, "close"), context=context)

    # --- Computer ---------------------------------------------------------

    def computer_click(
        self,
        serialno: str,
        x: int,
        y: int,
        button: str | None = None,
        context: Any = None,
    ) -> dict[str, Any]:
        """Click at absolute screen coordinates (button defaults to left)."""
        body: dict[str, Any] = {"x": x, "y": y}
        if button:
            body["button"] = button
        return self._request("POST", computer_path(serialno, "click"), context=context, json=body)

    def computer_double_click(
        self, serialno: str, x: int, y: int, context: Any = None
    ) -> dict[str, Any]:
        """Double click at absolute screen coordinates."""
        return self._request(
            "POST", computer_path(serialno, "double_click"), context=context, json={"x": x, "y": y}
        )

    def computer_long_click(
        self, serialno: str, x: int, y: int, duration: int = 0, context: Any = None
    ) -> dict[str, Any]:
        """Press and hold at coordinates; duration is in seconds."""
        body: dict[str, Any] = {"x": x, "y": y}
        if duration:
            body["duration"] = duration
        return self._request(
            "POST", computer_path(serialno, "long_click"), context=context, json=body
        )

    def computer_move(self, serialno: str, x: int, y: int, context: Any = None) -> dict[str, Any]:
        """Move the mouse without clicking."""
        return self._request(
            "POST", computer_path(serialno, "move"), context=context, json={"x": x, "y": y}
        )

    def computer_drag(
        self, serialno: str, x1: int, y1: int, x2: int, y2: int, context: Any = None
    ) -> dict[str, Any]:
        """Press at the first point, move to the second, release."""
        return self._request(
            "POST",
            computer_path(serialno, "drag"),
            context=context,
            json={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        )

    def computer_scroll(
        self,
        serialno: str,
        direction: str,
        amount: int = 0,
        context: Any = None,
    ) -> dict[str, Any]:
        """Scroll the mouse wheel; direction is up|down|left|right."""
        body: dict[str, Any] = {"direction": direction}
        if amount:
            body["amount"] = amount
        return self._request("POST", computer_path(serialno, "scroll"), context=context, json=body)

    def computer_type_text(self, serialno: str, text: str, context: Any = None) -> dict[str, Any]:
        """Type text at the current caret."""
        return self._request(
            "POST", computer_path(serialno, "type_text"), context=context, json={"text": text}
        )

    def computer_press(self, serialno: str, key: str, context: Any = None) -> dict[str, Any]:
        """Press a key, e.g. Enter or F5."""
        return self._request(
            "POST", computer_path(serialno, "press"), context=context, json={"key": key}
        )

    def computer_hotkey(
        self, serialno: str, keys: list[str], context: Any = None
    ) -> dict[str, Any]:
        """Press the given keys together."""
        return self._request(
            "POST", computer_path(serialno, "hotkey"), context=context, json={"keys": keys}
        )

    def computer_position(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get the current mouse position."""
        return self._request("GET", computer_path(serialno, "position"), context=context)

    def computer_screen_size(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get the primary screen size."""
        return self._request("GET", computer_path(serialno, "screen_size"), context=context)

    def computer_permissions(self, serialno: str, context: Any = None) -> dict[str, Any]:
        """Get the desktop-control permission status."""
        return self._request("GET", computer_path(serialno, "permissions"), context=context)

    def computer_launch_app(
        self, serialno: str, app_name: str, context: Any = None
    ) -> dict[str, Any]:
        """Launch a desktop application."""
        return self._request(
            "POST",
            computer_path(serialno, "launch_app"),
            context=context,
            json={"app_name": app_name},
        )

    def computer_wait(
        self, serialno: str, milliseconds: int, context: Any = None
    ) -> dict[str, Any]:
        """Block for a duration in milliseconds.

        The deadline is widened to cover the wait itself — the shared 30s
        default would abort any wait longer than that.
        """
        return self._request(
            "POST",
            computer_path(serialno, "wait"),
            context=context,
            timeout=wait_timeout(milliseconds),
            json={"seconds": milliseconds / 1000},
        )

    def computer_bash(
        self,
        serialno: str,
        command: str,
        timeout_seconds: int = 0,
        context: Any = None,
    ) -> dict[str, Any]:
        """Run a shell command on the host machine.

        The command runs as the desktop user, unsandboxed, under the platform
        default shell — treat it as shell access. ``timeout_seconds`` is the
        server-side budget; zero lets the server apply its 120s default. The
        command's own exit status arrives as ``data.exitCode``.
        """
        body: dict[str, Any] = {"command": command}
        if timeout_seconds:
            body["timeout"] = timeout_seconds
        return self._request(
            "POST",
            computer_path(serialno, "bash"),
            context=context,
            timeout=bash_timeout(timeout_seconds),
            json=body,
        )

    # --- Cross-family -----------------------------------------------------

    def screenshot_bytes(self, serialno: str, context: Any = None) -> bytes:
        """Capture a screenshot and return the raw image bytes.

        Screenshot is a cross-family action: it does not live under
        ``/api/browser/*`` or ``/api/computer/*``. The server dispatches
        ``/v1/screen/{serialno}`` by device type — computer → full-desktop
        capture, browser → CDP capture, otherwise the device image queue — so
        one call serves every platform.

        The server decides the image format (JPEG).
        """
        return self._request_bytes("POST", mobile_path(serialno, "screen"), context=context)

    def screenshot(self, serialno: str, context: Any = None) -> str:
        """Capture a screenshot, as a base64-encoded image.

        See :meth:`screenshot_bytes` for the raw form.
        """
        data = self.screenshot_bytes(serialno, context=context)
        return base64.b64encode(data).decode("ascii")
