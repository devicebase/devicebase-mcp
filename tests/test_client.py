"""Tests for the Devicebase API client."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from devicebase_mcp.client import DevicebaseClient


@pytest.fixture
def mock_httpx_response() -> Mock:
    """Create a mock HTTP response."""
    response = Mock()
    response.json.return_value = {"code": 200, "message": "success"}
    response.raise_for_status = Mock()
    return response


class TestDevicebaseClient:
    """Tests for DevicebaseClient."""

    def test_init(self) -> None:
        """Test client initialization."""
        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.test.cn"

    def test_default_base_url(self) -> None:
        """Test default base URL is set correctly."""
        client = DevicebaseClient(api_key="test-key")
        assert client.base_url == "https://api.devicebase.cn"

    @patch("devicebase_mcp.client.httpx.Client")
    def test_list_devices(
        self, mock_client_class: MagicMock, mock_httpx_response: Mock
    ) -> None:
        """Test listing devices."""
        mock_client = MagicMock()
        mock_client.request.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        result = client.list_devices(keyword="iPhone", state="free", limit=5)

        assert result == {"code": 200, "message": "success"}
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "/devices" in call_args[0][1]
        assert call_args[1]["params"]["keyword"] == "iPhone"
        assert call_args[1]["params"]["state"] == "free"

    @patch("devicebase_mcp.client.httpx.Client")
    def test_tap(self, mock_client_class: MagicMock, mock_httpx_response: Mock) -> None:
        """Test tap operation."""
        mock_client = MagicMock()
        mock_client.request.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        result = client.tap("ABC123", 100, 200)

        assert result == {"code": 200, "message": "success"}
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "/tap/ABC123" in call_args[0][1]
        assert call_args[1]["json"] == {"x": 100, "y": 200}

    @patch("devicebase_mcp.client.httpx.Client")
    def test_swipe(self, mock_client_class: MagicMock, mock_httpx_response: Mock) -> None:
        """Test swipe operation."""
        mock_client = MagicMock()
        mock_client.request.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        result = client.swipe("ABC123", 100, 200, 300, 400, 500)

        assert result == {"code": 200, "message": "success"}
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "/swipe/ABC123" in call_args[0][1]
        assert call_args[1]["json"] == {
            "x1": 100,
            "y1": 200,
            "x2": 300,
            "y2": 400,
            "duration": 500,
        }

    @patch("devicebase_mcp.client.httpx.Client")
    def test_launch_app(
        self, mock_client_class: MagicMock, mock_httpx_response: Mock
    ) -> None:
        """Test launch app operation."""
        mock_client = MagicMock()
        mock_client.request.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        result = client.launch_app("ABC123", "com.example.app")

        assert result == {"code": 200, "message": "success"}
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "/launch_app/ABC123" in call_args[0][1]
        assert call_args[1]["json"] == {"package": "com.example.app"}

    @patch("devicebase_mcp.client.httpx.Client")
    def test_screenshot(
        self, mock_client_class: MagicMock, mock_httpx_response: Mock
    ) -> None:
        """Test screenshot operation returns base64-encoded image."""
        import base64

        fake_image = b"\x89PNG\r\n\x1a\n"  # PNG header bytes
        mock_httpx_response.content = fake_image
        mock_client = MagicMock()
        mock_client.request.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        result = client.screenshot("ABC123")

        assert result == base64.b64encode(fake_image).decode("ascii")
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "/screen/ABC123" in call_args[0][1]

    @patch("devicebase_mcp.client.httpx.Client")
    def test_dump_hierarchy(
        self, mock_client_class: MagicMock, mock_httpx_response: Mock
    ) -> None:
        """Test dump hierarchy operation."""
        mock_httpx_response.json.return_value = {
            "hierarchy": {"node": "root", "children": []}
        }
        mock_client = MagicMock()
        mock_client.request.return_value = mock_httpx_response
        mock_client_class.return_value = mock_client

        client = DevicebaseClient(api_key="test-key", base_url="https://api.test.cn")
        result = client.dump_hierarchy("ABC123")

        assert "hierarchy" in result
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "/dump_hierarchy/ABC123" in call_args[0][1]
