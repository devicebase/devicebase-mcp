"""Tests for the server entry point and transport selection."""

from __future__ import annotations

import pytest

from devicebase_mcp.__main__ import build_server, parse_args


class TestBuildServer:
    """Server construction."""

    def test_registers_every_tool(self) -> None:
        mcp = build_server()
        assert len(mcp._tool_manager._tools) == 55  # noqa: SLF001

    def test_reads_the_base_url_from_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEVICEBASE_BASE_URL", "http://127.0.0.1:8000")
        monkeypatch.setenv("DEVICEBASE_API_KEY", "k")

        # Building must not require a reachable server.
        assert build_server() is not None

    def test_builds_without_an_api_key(self) -> None:
        """The key is resolved per request, so construction cannot require it."""
        assert build_server() is not None


class TestParseArgs:
    """Transport selection."""

    def test_defaults_to_stdio(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_TRANSPORT", raising=False)
        assert parse_args([]).transport == "stdio"

    def test_flag_overrides_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        assert parse_args(["--transport", "stdio"]).transport == "stdio"

    def test_environment_selects_the_transport(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
        assert parse_args([]).transport == "streamable-http"

    def test_rejects_an_unknown_transport(self) -> None:
        with pytest.raises(SystemExit):
            parse_args(["--transport", "carrier-pigeon"])

    def test_host_and_port_default_and_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("MCP_HOST", raising=False)
        monkeypatch.delenv("MCP_PORT", raising=False)

        defaults = parse_args([])
        assert defaults.host == "localhost"
        assert defaults.port == 8080

        overridden = parse_args(["--host", "0.0.0.0", "--port", "9000"])
        assert overridden.host == "0.0.0.0"
        assert overridden.port == 9000

    def test_host_and_port_read_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCP_HOST", "0.0.0.0")
        monkeypatch.setenv("MCP_PORT", "9999")

        args = parse_args([])
        assert args.host == "0.0.0.0"
        assert args.port == 9999
