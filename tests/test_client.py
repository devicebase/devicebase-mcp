"""Tests for the Devicebase API client."""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

from devicebase_mcp.client import (
    DevicebaseClient,
    bash_timeout,
    browser_path,
    computer_path,
    mobile_path,
    wait_timeout,
)
from devicebase_mcp.errors import (
    AuthenticationError,
    BusinessError,
    DeviceNotFoundError,
    ValidationError,
)

MOBILE = "db-mttul4i41di8"
BROWSER = "db-mtsi49bf0mqb"
COMPUTER = "db-mtthisv311f1"


def _response(payload: Any = None, *, content: bytes | None = None, status: int = 200) -> Mock:
    """Build a mock httpx response.

    ``text`` and ``content`` have to agree, because the client inspects the raw
    text for an envelope error before decoding it as JSON — a mock whose text is
    a Python repr would silently skip that check.
    """
    if content is None:
        content = json.dumps(payload if payload is not None else {}).encode()
    response = Mock()
    response.status_code = status
    response.content = content
    response.text = content.decode("utf-8", "replace")
    response.json.return_value = payload if payload is not None else {}
    return response


def _client(response: Mock | None = None) -> tuple[DevicebaseClient, MagicMock]:
    """Return a client whose httpx transport is a mock, plus that mock."""
    mock_http = MagicMock()
    mock_http.request.return_value = response or _response({"code": 200, "message": "success"})
    with patch("devicebase_mcp.client.httpx.Client", return_value=mock_http):
        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
    return client, mock_http


def _call(mock_http: MagicMock) -> tuple[str, str, dict[str, Any]]:
    """Return (method, url, kwargs) for the last request."""
    args, kwargs = mock_http.request.call_args
    return args[0], args[1], kwargs


def _headers(mock_http: MagicMock) -> dict[str, str]:
    """Return the ``headers`` kwarg passed to ``httpx.Client.request``."""
    return dict(_call(mock_http)[2]["headers"])


# The full request contract, as (client method, args, method, path, json, params).
REQUEST_TABLE: list[tuple[str, tuple, str, str, dict | None, dict | None]] = [
    # --- Mobile: /v1/{action}/{serialno} ---
    ("mobile_device_info", (MOBILE,), "POST", f"/v1/deviceinfo/{MOBILE}", None, None),
    ("mobile_tap", (MOBILE, 100, 200), "POST", f"/v1/tap/{MOBILE}", {"x": 100, "y": 200}, None),
    (
        "mobile_double_tap",
        (MOBILE, 1, 2),
        "POST",
        f"/v1/double_tap/{MOBILE}",
        {"x": 1, "y": 2},
        None,
    ),
    (
        "mobile_long_press",
        (MOBILE, 3, 4),
        "POST",
        f"/v1/long_press/{MOBILE}",
        {"x": 3, "y": 4},
        None,
    ),
    (
        "mobile_swipe",
        (MOBILE, 0, 100, 300, 100),
        "POST",
        f"/v1/swipe/{MOBILE}",
        # The contract has no duration field on swipe.
        {"x1": 0, "y1": 100, "x2": 300, "y2": 100},
        None,
    ),
    ("mobile_back", (MOBILE,), "POST", f"/v1/back/{MOBILE}", None, None),
    ("mobile_home", (MOBILE,), "POST", f"/v1/home/{MOBILE}", None, None),
    (
        "mobile_launch_app",
        (MOBILE, "com.tencent.mm"),
        "POST",
        f"/v1/launch_app/{MOBILE}",
        # The contract field is app_name; the old client sent package.
        {"app_name": "com.tencent.mm"},
        None,
    ),
    (
        "mobile_stop_app",
        (MOBILE, "com.tencent.mm"),
        "POST",
        f"/v1/stop_app/{MOBILE}",
        {"app_name": "com.tencent.mm"},
        None,
    ),
    ("mobile_stop_current_app", (MOBILE,), "POST", f"/v1/stop_current_app/{MOBILE}", None, None),
    ("mobile_current_app", (MOBILE,), "POST", f"/v1/current_app/{MOBILE}", None, None),
    ("mobile_input_text", (MOBILE, "hi"), "POST", f"/v1/input/{MOBILE}", {"text": "hi"}, None),
    ("mobile_clear_text", (MOBILE,), "POST", f"/v1/clear_text/{MOBILE}", None, None),
    ("mobile_bash", (MOBILE, "ls"), "POST", f"/v1/bash/{MOBILE}", {"command": "ls"}, None),
    ("mobile_dump_hierarchy", (MOBILE,), "POST", f"/v1/dump_hierarchy/{MOBILE}", None, None),
    (
        "mobile_install_app",
        (MOBILE, "/tmp/a.apk"),
        "POST",
        f"/v1/install_app/{MOBILE}",
        {"app_path": "/tmp/a.apk"},
        None,
    ),
    (
        "mobile_install_status",
        (MOBILE, "i-1"),
        "GET",
        f"/v1/install_status/{MOBILE}",
        None,
        {"install_id": "i-1"},
    ),
    # --- Browser: /api/browser/{serialno}/{action} ---
    (
        "browser_navigate",
        (BROWSER, "https://example.com"),
        "POST",
        f"/api/browser/{BROWSER}/navigate",
        {"url": "https://example.com"},
        None,
    ),
    ("browser_refresh", (BROWSER,), "POST", f"/api/browser/{BROWSER}/refresh", None, None),
    ("browser_go_back", (BROWSER,), "POST", f"/api/browser/{BROWSER}/go_back", None, None),
    ("browser_go_forward", (BROWSER,), "POST", f"/api/browser/{BROWSER}/go_forward", None, None),
    (
        "browser_input",
        (BROWSER, "hi"),
        "POST",
        f"/api/browser/{BROWSER}/input",
        {"text": "hi"},
        None,
    ),
    (
        "browser_click",
        (BROWSER, "#a"),
        "POST",
        f"/api/browser/{BROWSER}/click",
        {"selector": "#a"},
        None,
    ),
    (
        "browser_fill",
        (BROWSER, "#a", "v"),
        "POST",
        f"/api/browser/{BROWSER}/fill",
        {"selector": "#a", "value": "v"},
        None,
    ),
    (
        "browser_select",
        (BROWSER, "#a", "v"),
        "POST",
        f"/api/browser/{BROWSER}/select",
        {"selector": "#a", "value": "v"},
        None,
    ),
    # The read-only DOM actions are GETs carrying the selector as a query param.
    (
        "browser_text",
        (BROWSER, "#a"),
        "GET",
        f"/api/browser/{BROWSER}/text",
        None,
        {"selector": "#a"},
    ),
    (
        "browser_attribute",
        (BROWSER, "#a", "href"),
        "GET",
        f"/api/browser/{BROWSER}/attribute",
        None,
        {"selector": "#a", "attribute": "href"},
    ),
    (
        "browser_exists",
        (BROWSER, ".m"),
        "GET",
        f"/api/browser/{BROWSER}/exists",
        None,
        {"selector": ".m"},
    ),
    (
        "browser_execute",
        (BROWSER, "1"),
        "POST",
        f"/api/browser/{BROWSER}/execute",
        {"script": "1"},
        None,
    ),
    (
        "browser_hotkey",
        (BROWSER, ["Meta", "a"]),
        "POST",
        f"/api/browser/{BROWSER}/hotkey",
        {"keys": ["Meta", "a"]},
        None,
    ),
    ("browser_state", (BROWSER,), "GET", f"/api/browser/{BROWSER}/state", None, None),
    ("browser_tabs", (BROWSER,), "GET", f"/api/browser/{BROWSER}/tabs", None, None),
    (
        "browser_tab_open",
        (BROWSER, "https://example.com"),
        "POST",
        f"/api/browser/{BROWSER}/tab/open",
        {"url": "https://example.com"},
        None,
    ),
    (
        "browser_tab_close",
        (BROWSER, "t1"),
        "POST",
        f"/api/browser/{BROWSER}/tab/close",
        {"tab_id": "t1"},
        None,
    ),
    (
        "browser_tab_close_all",
        (BROWSER,),
        "POST",
        f"/api/browser/{BROWSER}/tab/close_all",
        None,
        None,
    ),
    (
        "browser_tab_switch",
        (BROWSER, "t1"),
        "POST",
        f"/api/browser/{BROWSER}/tab/switch",
        {"tab_id": "t1"},
        None,
    ),
    ("browser_launch", (BROWSER,), "POST", f"/api/browser/{BROWSER}/launch", None, None),
    ("browser_close", (BROWSER,), "POST", f"/api/browser/{BROWSER}/close", None, None),
    # --- Computer: /api/computer/{serialno}/{action} ---
    (
        "computer_click",
        (COMPUTER, 1, 2),
        "POST",
        f"/api/computer/{COMPUTER}/click",
        # An omitted button lets the server default to left.
        {"x": 1, "y": 2},
        None,
    ),
    (
        "computer_double_click",
        (COMPUTER, 1, 2),
        "POST",
        f"/api/computer/{COMPUTER}/double_click",
        {"x": 1, "y": 2},
        None,
    ),
    (
        "computer_long_click",
        (COMPUTER, 1, 2),
        "POST",
        f"/api/computer/{COMPUTER}/long_click",
        {"x": 1, "y": 2},
        None,
    ),
    (
        "computer_move",
        (COMPUTER, 1, 2),
        "POST",
        f"/api/computer/{COMPUTER}/move",
        {"x": 1, "y": 2},
        None,
    ),
    (
        "computer_drag",
        (COMPUTER, 1, 2, 3, 4),
        "POST",
        f"/api/computer/{COMPUTER}/drag",
        {"x1": 1, "y1": 2, "x2": 3, "y2": 4},
        None,
    ),
    (
        "computer_scroll",
        (COMPUTER, "down"),
        "POST",
        f"/api/computer/{COMPUTER}/scroll",
        {"direction": "down"},
        None,
    ),
    (
        "computer_type_text",
        (COMPUTER, "hi"),
        "POST",
        f"/api/computer/{COMPUTER}/type_text",
        {"text": "hi"},
        None,
    ),
    (
        "computer_press",
        (COMPUTER, "Enter"),
        "POST",
        f"/api/computer/{COMPUTER}/press",
        {"key": "Enter"},
        None,
    ),
    (
        "computer_hotkey",
        (COMPUTER, ["Meta"]),
        "POST",
        f"/api/computer/{COMPUTER}/hotkey",
        {"keys": ["Meta"]},
        None,
    ),
    ("computer_position", (COMPUTER,), "GET", f"/api/computer/{COMPUTER}/position", None, None),
    (
        "computer_screen_size",
        (COMPUTER,),
        "GET",
        f"/api/computer/{COMPUTER}/screen_size",
        None,
        None,
    ),
    (
        "computer_permissions",
        (COMPUTER,),
        "GET",
        f"/api/computer/{COMPUTER}/permissions",
        None,
        None,
    ),
    (
        "computer_launch_app",
        (COMPUTER, "Code"),
        "POST",
        f"/api/computer/{COMPUTER}/launch_app",
        {"app_name": "Code"},
        None,
    ),
    # wait takes ms from the caller and sends seconds on the wire.
    (
        "computer_wait",
        (COMPUTER, 2500),
        "POST",
        f"/api/computer/{COMPUTER}/wait",
        {"seconds": 2.5},
        None,
    ),
    (
        "computer_bash",
        (COMPUTER, "ls"),
        "POST",
        f"/api/computer/{COMPUTER}/bash",
        {"command": "ls"},
        None,
    ),
]


class TestRequestContract:
    """Every client method must hit the documented method, path and body."""

    @pytest.mark.parametrize(
        ("method", "args", "http_method", "path", "body", "params"),
        REQUEST_TABLE,
        ids=[case[0] for case in REQUEST_TABLE],
    )
    def test_request(
        self,
        method: str,
        args: tuple,
        http_method: str,
        path: str,
        body: dict | None,
        params: dict | None,
    ) -> None:
        client, mock_http = _client()
        getattr(client, method)(*args)

        actual_method, url, kwargs = _call(mock_http)
        assert actual_method == http_method
        assert url == f"https://api.test.cn{path}"

        if body is None:
            assert kwargs.get("json") is None
        else:
            assert kwargs["json"] == body

        if params is None:
            assert not kwargs.get("params")
        else:
            assert kwargs["params"] == params


class TestPaths:
    """Path builders."""

    def test_mobile_path(self) -> None:
        assert mobile_path(MOBILE, "tap") == f"/v1/tap/{MOBILE}"

    def test_browser_path(self) -> None:
        assert browser_path(BROWSER, "tab/open") == f"/api/browser/{BROWSER}/tab/open"

    def test_computer_path(self) -> None:
        assert computer_path(COMPUTER, "click") == f"/api/computer/{COMPUTER}/click"

    def test_serialnos_are_url_escaped(self) -> None:
        assert mobile_path("a b/c", "tap") == "/v1/tap/a%20b%2Fc"


class TestListDevices:
    """Device discovery."""

    def test_forwards_every_filter(self) -> None:
        client, mock_http = _client()
        client.list_devices(keyword="Pixel", state="free", device_type="mobile", limit=5)

        _, _, kwargs = _call(mock_http)
        assert kwargs["params"] == {
            "keyword": "Pixel",
            "state": "free",
            "type": "mobile",
            "limit": 5,
        }

    def test_omits_unset_filters(self) -> None:
        client, mock_http = _client()
        client.list_devices(limit=None)

        _, _, kwargs = _call(mock_http)
        assert kwargs["params"] == {}


class TestTimeouts:
    """Blocking actions widen their own deadline."""

    def test_wait_outlasts_the_requested_wait(self) -> None:
        assert wait_timeout(0) == 15.0
        assert wait_timeout(2500) == 2.5 + 15.0
        assert wait_timeout(-5) == 15.0

    def test_bash_outlasts_the_requested_timeout(self) -> None:
        # An omitted timeout still has to outlast the server's 120s default.
        assert bash_timeout(0) == 135.0
        assert bash_timeout(-1) == 135.0
        assert bash_timeout(30) == 45.0

    def test_wait_sends_an_extended_timeout(self) -> None:
        client, mock_http = _client()
        client.computer_wait(COMPUTER, 2500)

        _, _, kwargs = _call(mock_http)
        assert kwargs["timeout"] == 2.5 + 15.0

    def test_bash_sends_an_extended_timeout(self) -> None:
        client, mock_http = _client()
        client.computer_bash(COMPUTER, "ls", 600)

        _, _, kwargs = _call(mock_http)
        assert kwargs["timeout"] == 615.0

    def test_ordinary_actions_use_the_shared_default(self) -> None:
        client, mock_http = _client()
        client.mobile_tap(MOBILE, 1, 2)

        _, _, kwargs = _call(mock_http)
        assert "timeout" not in kwargs


class TestFailureLayers:
    """Both error layers must surface."""

    def test_envelope_error_on_an_http_200(self) -> None:
        client, _ = _client(_response({"code": 502, "message": "-32602: Invalid parameters"}))
        with pytest.raises(BusinessError) as excinfo:
            client.mobile_tap(MOBILE, 1, 2)
        assert excinfo.value.code == 502

    def test_envelope_codes_in_the_2xx_range_pass(self) -> None:
        client, _ = _client(_response({"code": 200, "message": "success"}))
        assert client.mobile_tap(MOBILE, 1, 2) == {"code": 200, "message": "success"}

    def test_non_envelope_bodies_are_left_alone(self) -> None:
        client, _ = _client(_response({"success": True}))
        assert client.mobile_tap(MOBILE, 1, 2) == {"success": True}

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, AuthenticationError),
            (404, DeviceNotFoundError),
            (400, ValidationError),
            (422, ValidationError),
        ],
    )
    def test_http_statuses_map_onto_errors(self, status: int, expected: type) -> None:
        client, _ = _client(_response({"code": status}, status=status))
        with pytest.raises(expected):
            client.mobile_tap(MOBILE, 1, 2)

    def test_errors_carry_the_server_body(self) -> None:
        response = _response(status=404)
        response.text = '{"code":404,"message":"设备不存在: nope"}'
        client, _ = _client(response)

        with pytest.raises(DeviceNotFoundError) as excinfo:
            client.mobile_tap(MOBILE, 1, 2)
        assert "API error (HTTP 404)" in str(excinfo.value)
        assert "设备不存在" in str(excinfo.value)


class TestScreenshot:
    """Screenshots are a cross-family POST."""

    def test_posts_and_returns_base64(self) -> None:
        jpeg = b"\xff\xd8\xff\xe0\x00\x10"
        client, mock_http = _client(_response(content=jpeg))

        result = client.screenshot(MOBILE)

        assert result == base64.b64encode(jpeg).decode("ascii")
        method, url, _ = _call(mock_http)
        assert method == "POST"
        assert url.endswith(f"/v1/screen/{MOBILE}")

    def test_bytes_form_is_available(self) -> None:
        jpeg = b"\xff\xd8\xff\xe0"
        client, _ = _client(_response(content=jpeg))
        assert client.screenshot_bytes(MOBILE) == jpeg


class TestAuthHeaderPrecedence:
    """Verify the headers > env > (empty) precedence for the Authorization header."""

    @staticmethod
    def _context(auth_header: str | None) -> SimpleNamespace:
        """Build a minimal MCP-like context matching the real SDK chain."""
        headers = {"Authorization": auth_header} if auth_header else {}
        starlette_request = SimpleNamespace(headers=headers)
        request_context = SimpleNamespace(request=starlette_request)
        return SimpleNamespace(request_context=request_context)

    def test_context_header_takes_precedence_over_env(self) -> None:
        client, mock_http = _client()
        client.mobile_tap(MOBILE, 1, 2, context=self._context("Bearer request-key"))

        assert _headers(mock_http)["Authorization"] == "Bearer request-key"

    def test_falls_back_to_env_when_no_context_header(self) -> None:
        client, mock_http = _client()
        client.mobile_tap(MOBILE, 1, 2, context=self._context(None))

        assert _headers(mock_http)["Authorization"] == "Bearer test-key"

    def test_falls_back_to_env_when_context_lacks_request(self) -> None:
        client, mock_http = _client()
        client.mobile_tap(MOBILE, 1, 2, context=object())

        assert _headers(mock_http)["Authorization"] == "Bearer test-key"

    def test_non_bearer_header_is_ignored(self) -> None:
        client, mock_http = _client()
        client.mobile_tap(MOBILE, 1, 2, context=self._context("Basic dXNlcjpwYXNz"))

        assert _headers(mock_http)["Authorization"] == "Bearer test-key"

    def test_bytes_endpoint_uses_same_precedence(self) -> None:
        client, mock_http = _client(_response(content=b"\xff\xd8"))
        client.screenshot(MOBILE, context=self._context("Bearer per-req"))

        assert _headers(mock_http)["Authorization"] == "Bearer per-req"


class TestConfiguration:
    """Client construction."""

    def test_reads_the_configured_values(self) -> None:
        client = DevicebaseClient(api_key="k", base_url="https://api.test.cn")
        assert client.api_key == "k"
        assert client.base_url == "https://api.test.cn"

    def test_default_base_url(self) -> None:
        assert DevicebaseClient(api_key="k").base_url == "https://api.devicebase.cn"

    def test_trims_trailing_slashes(self) -> None:
        assert DevicebaseClient(api_key="k", base_url="http://x/").base_url == "http://x"

    def test_missing_key_raises_before_sending(self) -> None:
        client, mock_http = _client()
        client.api_key = ""

        with pytest.raises(AuthenticationError):
            client.mobile_tap(MOBILE, 1, 2)
        mock_http.request.assert_not_called()
