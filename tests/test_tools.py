"""Tests for the MCP tool layer.

These drive the functions that are actually registered with FastMCP, so a tool
whose signature or delegation drifts is caught — a test that calls the client
mock directly would not notice.
"""

from __future__ import annotations

import base64
import inspect
import json
from unittest.mock import MagicMock

import pytest
from mcp.server.fastmcp import FastMCP

from devicebase_mcp.tools import register_all_tools
from devicebase_mcp.tools.device import describe_image_format

MOBILE = "db-mttul4i41di8"
BROWSER = "db-mtsi49bf0mqb"
COMPUTER = "db-mtthisv311f1"


def _tools(client: MagicMock | None = None) -> dict:
    """Register every tool against a mock client and return them by name."""
    mcp = FastMCP("Test")
    register_all_tools(mcp, client or MagicMock())
    return mcp._tool_manager._tools  # noqa: SLF001 - the only handle FastMCP exposes


def _client_call(client: MagicMock) -> tuple[str, tuple, dict]:
    """Return the (method name, args, kwargs) of the mock's last call."""
    name, args, kwargs = client.mock_calls[-1]
    return name, args, kwargs


# (tool name, call args, expected client method, positional args, keyword args)
DELEGATION_TABLE: list[tuple[str, tuple, str, tuple, dict]] = [
    # --- Cross-platform ---
    (
        "list_devices",
        (),
        "list_devices",
        (),
        {"keyword": None, "state": None, "device_type": None, "limit": 10},
    ),
    (
        "list_devices",
        ("Pixel", "free", "mobile", 5),
        "list_devices",
        (),
        {"keyword": "Pixel", "state": "free", "device_type": "mobile", "limit": 5},
    ),
    # --- Mobile ---
    (
        "mobile_device_info",
        (MOBILE,),
        "mobile_device_info",
        (MOBILE,),
        {},
    ),
    (
        "mobile_tap",
        (MOBILE, 1, 2),
        "mobile_tap",
        (MOBILE, 1, 2),
        {},
    ),
    (
        "mobile_double_tap",
        (MOBILE, 1, 2),
        "mobile_double_tap",
        (MOBILE, 1, 2),
        {},
    ),
    (
        "mobile_long_press",
        (MOBILE, 1, 2),
        "mobile_long_press",
        (MOBILE, 1, 2),
        {},
    ),
    (
        "mobile_swipe",
        (MOBILE, 1, 2, 3, 4),
        "mobile_swipe",
        (MOBILE, 1, 2, 3, 4),
        {},
    ),
    (
        "mobile_back",
        (MOBILE,),
        "mobile_back",
        (MOBILE,),
        {},
    ),
    (
        "mobile_home",
        (MOBILE,),
        "mobile_home",
        (MOBILE,),
        {},
    ),
    (
        "mobile_launch_app",
        (MOBILE, "app"),
        "mobile_launch_app",
        (MOBILE, "app"),
        {},
    ),
    (
        "mobile_stop_app",
        (MOBILE, "app"),
        "mobile_stop_app",
        (MOBILE, "app"),
        {},
    ),
    (
        "mobile_stop_current_app",
        (MOBILE,),
        "mobile_stop_current_app",
        (MOBILE,),
        {},
    ),
    (
        "mobile_current_app",
        (MOBILE,),
        "mobile_current_app",
        (MOBILE,),
        {},
    ),
    (
        "mobile_input_text",
        (MOBILE, "hi"),
        "mobile_input_text",
        (MOBILE, "hi"),
        {},
    ),
    (
        "mobile_clear_text",
        (MOBILE,),
        "mobile_clear_text",
        (MOBILE,),
        {},
    ),
    (
        "mobile_bash",
        (MOBILE, "ls"),
        "mobile_bash",
        (MOBILE, "ls"),
        {},
    ),
    (
        "mobile_dump_hierarchy",
        (MOBILE,),
        "mobile_dump_hierarchy",
        (MOBILE,),
        {},
    ),
    (
        "mobile_install_app",
        (MOBILE, "/tmp/a.apk"),
        "mobile_install_app",
        (MOBILE, "/tmp/a.apk"),
        {},
    ),
    (
        "mobile_install_status",
        (MOBILE, "i-1"),
        "mobile_install_status",
        (MOBILE, "i-1"),
        {},
    ),
    # --- Browser ---
    (
        "browser_navigate",
        (BROWSER, "https://x"),
        "browser_navigate",
        (BROWSER, "https://x"),
        {},
    ),
    (
        "browser_refresh",
        (BROWSER,),
        "browser_refresh",
        (BROWSER,),
        {},
    ),
    (
        "browser_go_back",
        (BROWSER,),
        "browser_go_back",
        (BROWSER,),
        {},
    ),
    (
        "browser_go_forward",
        (BROWSER,),
        "browser_go_forward",
        (BROWSER,),
        {},
    ),
    (
        "browser_input",
        (BROWSER, "hi"),
        "browser_input",
        (BROWSER, "hi"),
        {},
    ),
    (
        "browser_click",
        (BROWSER, "#a"),
        "browser_click",
        (BROWSER, "#a"),
        {},
    ),
    (
        "browser_fill",
        (BROWSER, "#a", "v"),
        "browser_fill",
        (BROWSER, "#a", "v"),
        {},
    ),
    (
        "browser_select",
        (BROWSER, "#a", "v"),
        "browser_select",
        (BROWSER, "#a", "v"),
        {},
    ),
    (
        "browser_text",
        (BROWSER, "#a"),
        "browser_text",
        (BROWSER, "#a"),
        {},
    ),
    (
        "browser_attribute",
        (BROWSER, "#a", "href"),
        "browser_attribute",
        (BROWSER, "#a", "href"),
        {},
    ),
    (
        "browser_exists",
        (BROWSER, "#a"),
        "browser_exists",
        (BROWSER, "#a"),
        {},
    ),
    (
        "browser_execute",
        (BROWSER, "1"),
        "browser_execute",
        (BROWSER, "1"),
        {},
    ),
    (
        "browser_hotkey",
        (BROWSER, ["Meta", "a"]),
        "browser_hotkey",
        (BROWSER, ["Meta", "a"]),
        {},
    ),
    (
        "browser_state",
        (BROWSER,),
        "browser_state",
        (BROWSER,),
        {},
    ),
    (
        "browser_tabs",
        (BROWSER,),
        "browser_tabs",
        (BROWSER,),
        {},
    ),
    (
        "browser_tab_open",
        (BROWSER, "https://x"),
        "browser_tab_open",
        (BROWSER, "https://x"),
        {},
    ),
    (
        "browser_tab_close",
        (BROWSER, "t1"),
        "browser_tab_close",
        (BROWSER, "t1"),
        {},
    ),
    (
        "browser_tab_close_all",
        (BROWSER,),
        "browser_tab_close_all",
        (BROWSER,),
        {},
    ),
    (
        "browser_tab_switch",
        (BROWSER, "t1"),
        "browser_tab_switch",
        (BROWSER, "t1"),
        {},
    ),
    (
        "browser_launch",
        (BROWSER,),
        "browser_launch",
        (BROWSER,),
        {},
    ),
    (
        "browser_close",
        (BROWSER,),
        "browser_close",
        (BROWSER,),
        {},
    ),
    # --- Computer ---
    (
        "computer_click",
        (COMPUTER, 1, 2),
        "computer_click",
        (COMPUTER, 1, 2),
        {"button": None},
    ),
    (
        "computer_click",
        (COMPUTER, 1, 2, "right"),
        "computer_click",
        (COMPUTER, 1, 2),
        {"button": "right"},
    ),
    (
        "computer_double_click",
        (COMPUTER, 1, 2),
        "computer_double_click",
        (COMPUTER, 1, 2),
        {},
    ),
    (
        "computer_long_click",
        (COMPUTER, 1, 2, 3),
        "computer_long_click",
        (COMPUTER, 1, 2, 3),
        {},
    ),
    (
        "computer_move",
        (COMPUTER, 1, 2),
        "computer_move",
        (COMPUTER, 1, 2),
        {},
    ),
    (
        "computer_drag",
        (COMPUTER, 1, 2, 3, 4),
        "computer_drag",
        (COMPUTER, 1, 2, 3, 4),
        {},
    ),
    (
        "computer_scroll",
        (COMPUTER, "down", 5),
        "computer_scroll",
        (COMPUTER, "down", 5),
        {},
    ),
    (
        "computer_type_text",
        (COMPUTER, "hi"),
        "computer_type_text",
        (COMPUTER, "hi"),
        {},
    ),
    (
        "computer_press",
        (COMPUTER, "Enter"),
        "computer_press",
        (COMPUTER, "Enter"),
        {},
    ),
    (
        "computer_hotkey",
        (COMPUTER, ["Meta"]),
        "computer_hotkey",
        (COMPUTER, ["Meta"]),
        {},
    ),
    (
        "computer_position",
        (COMPUTER,),
        "computer_position",
        (COMPUTER,),
        {},
    ),
    (
        "computer_screen_size",
        (COMPUTER,),
        "computer_screen_size",
        (COMPUTER,),
        {},
    ),
    (
        "computer_permissions",
        (COMPUTER,),
        "computer_permissions",
        (COMPUTER,),
        {},
    ),
    (
        "computer_launch_app",
        (COMPUTER, "Code"),
        "computer_launch_app",
        (COMPUTER, "Code"),
        {},
    ),
    (
        "computer_wait",
        (COMPUTER, 2500),
        "computer_wait",
        (COMPUTER, 2500),
        {},
    ),
    (
        "computer_bash",
        (COMPUTER, "ls", 30),
        "computer_bash",
        (COMPUTER, "ls", 30),
        {},
    ),
]


class TestRegistration:
    """The tool surface itself."""

    def test_registers_the_whole_contract(self) -> None:
        tools = _tools()
        assert len(tools) == 55

        prefixes = {"mobile": 0, "browser": 0, "computer": 0}
        for name in tools:
            for prefix in prefixes:
                if name.startswith(f"{prefix}_"):
                    prefixes[prefix] += 1

        assert prefixes == {"mobile": 17, "browser": 21, "computer": 15}
        # Two platform-agnostic tools.
        assert "list_devices" in tools
        assert "screenshot" in tools

    def test_every_tool_has_a_description(self) -> None:
        for name, tool in _tools().items():
            assert tool.description, f"{name} has no description"
            assert len(tool.description) > 30, f"{name}'s description is too thin"

    def test_tool_names_are_unique(self) -> None:
        names = list(_tools())
        assert len(names) == len(set(names))

    def test_no_tool_shadows_a_platform_action(self) -> None:
        """A bare `click`/`tap` would be ambiguous across three platforms."""
        tools = _tools()
        for ambiguous in ("tap", "click", "screenshot_", "bash"):
            assert ambiguous not in tools

    def test_no_tool_leaks_the_ctx_parameter(self) -> None:
        for name, tool in _tools().items():
            params = inspect.signature(tool.fn).parameters
            assert list(params)[-1] == "ctx", f"{name}: ctx must be the trailing parameter"


class TestDelegation:
    """Each tool must call its client method with the arguments it was given."""

    @pytest.mark.parametrize(
        ("tool_name", "args", "client_method", "client_args", "client_kwargs"),
        DELEGATION_TABLE,
        ids=[f"{case[0]}{case[1]}" for case in DELEGATION_TABLE],
    )
    def test_delegates(
        self,
        tool_name: str,
        args: tuple,
        client_method: str,
        client_args: tuple,
        client_kwargs: dict,
    ) -> None:
        client = MagicMock()
        # The tool serializes the client's return value.
        getattr(client, client_method).return_value = {"code": 200}

        result = _tools(client)[tool_name].fn(*args)

        name, call_args, call_kwargs = _client_call(client)
        assert name == client_method
        assert call_args == client_args
        # The MCP context rides along as a keyword argument on every call.
        assert call_kwargs.pop("context") is None
        assert call_kwargs == client_kwargs
        assert json.loads(result) == {"code": 200}


class TestScreenshot:
    """The cross-family screenshot tool."""

    def test_returns_base64_and_the_format(self) -> None:
        jpeg = b"\xff\xd8\xff\xe0\x00\x10"
        client = MagicMock()
        client.screenshot_bytes.return_value = jpeg

        payload = json.loads(_tools(client)["screenshot"].fn(MOBILE))

        assert payload["image_format"] == "jpeg"
        assert base64.b64decode(payload["image_base64"]) == jpeg
        assert client.screenshot_bytes.call_args[0] == (MOBILE,)

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (b"\xff\xd8\xff\xe0", "jpeg"),
            (b"\x89PNG\r\n\x1a\n", "png"),
            (b"GIF87a", "gif"),
            (b"GIF89a", "gif"),
            (b"RIFF\x00\x00\x00\x00WEBP", "webp"),
            (b"\x00\x01\x02\x03", "unknown"),
            (b"", "unknown"),
        ],
    )
    def test_format_sniffing(self, data: bytes, expected: str) -> None:
        assert describe_image_format(data) == expected


class TestArguments:
    """Argument handling the tools are responsible for."""

    def test_list_devices_defaults(self) -> None:
        client = MagicMock()
        client.list_devices.return_value = {"code": 200}

        _tools(client)["list_devices"].fn()

        _, call_args, call_kwargs = _client_call(client)
        assert call_args == ()
        assert call_kwargs["keyword"] is None
        assert call_kwargs["state"] is None
        assert call_kwargs["device_type"] is None
        assert call_kwargs["limit"] == 10

    def test_computer_click_omits_the_button_by_default(self) -> None:
        client = MagicMock()
        client.computer_click.return_value = {"code": 200}

        _tools(client)["computer_click"].fn(COMPUTER, 1, 2)

        assert _client_call(client)[2]["button"] is None

    def test_computer_long_click_defaults_to_the_driver_default(self) -> None:
        client = MagicMock()
        client.computer_long_click.return_value = {"code": 200}

        _tools(client)["computer_long_click"].fn(COMPUTER, 1, 2)

        assert _client_call(client)[1] == (COMPUTER, 1, 2, 0)

    def test_computer_bash_defaults_to_the_server_timeout(self) -> None:
        client = MagicMock()
        client.computer_bash.return_value = {"code": 200}

        _tools(client)["computer_bash"].fn(COMPUTER, "ls")

        assert _client_call(client)[1] == (COMPUTER, "ls", 0)

    def test_unicode_survives_serialization(self) -> None:
        client = MagicMock()
        client.mobile_input_text.return_value = {"code": 200, "data": {"echo": "你好 世界"}}

        result = _tools(client)["mobile_input_text"].fn(MOBILE, "你好 世界")

        # ensure_ascii=False keeps the text readable rather than escaping it.
        assert "你好 世界" in result
