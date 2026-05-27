"""Tests for MCP tools."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from devicebase_mcp.client import DevicebaseClient


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock client."""
    return MagicMock(spec=DevicebaseClient)


class TestDeviceTools:
    """Tests for device management tools."""

    def test_list_devices_output(self, mock_client: MagicMock) -> None:
        """Test list_devices tool output format."""
        mock_client.list_devices.return_value = {
            "data": [{"serial": "ABC123", "name": "iPhone 15 Pro"}]
        }

        result = mock_client.list_devices(keyword="iPhone", state="free", limit=10)

        assert "data" in result
        assert len(result["data"]) == 1
        assert result["data"][0]["serial"] == "ABC123"

    def test_get_device_info_output(self, mock_client: MagicMock) -> None:
        """Test get_device_info tool output format."""
        mock_client.device_info.return_value = {
            "serial": "ABC123",
            "brand": "Apple",
            "model": "iPhone 15 Pro",
        }

        result = mock_client.device_info("ABC123")

        assert result["serial"] == "ABC123"
        assert result["brand"] == "Apple"


class TestTouchTools:
    """Tests for touch interaction tools."""

    def test_tap(self, mock_client: MagicMock) -> None:
        """Test tap tool calls client correctly."""
        mock_client.tap.return_value = {"success": True}

        mock_client.tap("ABC123", 100, 200)

        mock_client.tap.assert_called_once_with("ABC123", 100, 200)

    def test_swipe(self, mock_client: MagicMock) -> None:
        """Test swipe tool calls client correctly."""
        mock_client.swipe.return_value = {"success": True}

        mock_client.swipe("ABC123", 100, 200, 300, 400, 500)

        mock_client.swipe.assert_called_once_with("ABC123", 100, 200, 300, 400, 500)


class TestAppTools:
    """Tests for app management tools."""

    def test_launch_app(self, mock_client: MagicMock) -> None:
        """Test launch_app tool calls client correctly."""
        mock_client.launch_app.return_value = {"success": True}

        mock_client.launch_app("ABC123", "com.example.app")

        mock_client.launch_app.assert_called_once_with("ABC123", "com.example.app")

    def test_get_current_app(self, mock_client: MagicMock) -> None:
        """Test get_current_app tool returns correct format."""
        mock_client.current_app.return_value = {
            "package": "com.example.app",
            "activity": "MainActivity",
        }

        result = mock_client.current_app("ABC123")

        assert result["package"] == "com.example.app"
        assert result["activity"] == "MainActivity"


class TestUITools:
    """Tests for UI inspection tools."""

    def test_screenshot(self, mock_client: MagicMock) -> None:
        """Test screenshot tool returns base64 data."""
        mock_client.screenshot.return_value = "base64data..."

        result = mock_client.screenshot("ABC123")

        assert result == "base64data..."

    def test_dump_hierarchy(self, mock_client: MagicMock) -> None:
        """Test dump_hierarchy tool returns JSON structure."""
        mock_client.dump_hierarchy.return_value = {
            "hierarchy": {"node": "root", "children": []}
        }

        result = mock_client.dump_hierarchy("ABC123")

        assert "hierarchy" in result
