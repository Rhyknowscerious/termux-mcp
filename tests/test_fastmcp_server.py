"""
Unit tests for the FastMCP-based Termux MCP server.

These tests verify that the FastMCP tools work correctly by mocking
the execute_command function and testing tool execution.
"""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastmcp import Client


@pytest.fixture
def mock_execute_command():
    """Mock execute_command for testing tool handlers."""
    with patch("termux_mcp.mcp_server_fastmcp.execute_command") as mock:
        yield mock


@pytest.fixture
def mcp_server():
    """Get the FastMCP server instance."""
    from termux_mcp.mcp_server_fastmcp import mcp
    return mcp


class TestFastMcpServerInitialization:
    """Tests for FastMCP server initialization."""

    def test_server_name(self, mcp_server):
        """Test that server has correct name."""
        assert mcp_server.name == "termux-mcp"

    def test_server_version(self, mcp_server):
        """Test that server has correct version."""
        assert mcp_server.version == "2.0.0"

    def test_server_has_instructions(self, mcp_server):
        """Test that server has instructions."""
        assert mcp_server.instructions is not None
        assert len(mcp_server.instructions) > 0


class TestFastMcpToolsList:
    """Tests for FastMCP tools listing."""

    @pytest.mark.asyncio
    async def test_tools_count(self, mcp_server):
        """Test that all 10 tools are registered."""
        tools = await mcp_server._local_provider.list_tools()
        tool_names = {tool.name for tool in tools}
        
        expected_tools = {
            "run_command",
            "get_battery",
            "get_location",
            "list_sms",
            "get_clipboard",
            "set_clipboard",
            "show_toast",
            "get_wifi_info",
            "list_contacts",
            "get_device_info",
        }
        
        assert tool_names == expected_tools
        assert len(tools) == 10

    @pytest.mark.asyncio
    async def test_each_tool_has_description(self, mcp_server):
        """Test that each tool has a description."""
        tools = await mcp_server._local_provider.list_tools()
        
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_run_command_tool_schema(self, mcp_server):
        """Test run_command tool has correct input schema."""
        tools = await mcp_server._local_provider.list_tools()
        run_command = next(t for t in tools if t.name == "run_command")
        
        # Check parameters
        assert "cmd" in run_command.parameters["properties"]
        assert "timeout" in run_command.parameters["properties"]
        assert run_command.parameters["properties"]["timeout"]["default"] == 30

    @pytest.mark.asyncio
    async def test_get_location_tool_schema(self, mcp_server):
        """Test get_location tool has correct input schema."""
        tools = await mcp_server._local_provider.list_tools()
        get_location = next(t for t in tools if t.name == "get_location")
        
        # Check parameters
        assert "provider" in get_location.parameters["properties"]
        assert get_location.parameters["properties"]["provider"]["default"] == "gps"

    @pytest.mark.asyncio
    async def test_list_sms_tool_schema(self, mcp_server):
        """Test list_sms tool has correct input schema."""
        tools = await mcp_server._local_provider.list_tools()
        list_sms = next(t for t in tools if t.name == "list_sms")
        
        # Check parameters
        assert "limit" in list_sms.parameters["properties"]
        assert list_sms.parameters["properties"]["limit"]["default"] == 10


class TestFastMcpToolExecution:
    """Tests for FastMCP tool execution."""

    @pytest.mark.asyncio
    async def test_run_command_success(self, mock_execute_command):
        """Test run_command tool executes command successfully."""
        from termux_mcp.mcp_server_fastmcp import run_command
        
        mock_execute_command.return_value = (0, "test output")
        
        # Create a mock context
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.warning = MagicMock()
        
        result = run_command(mock_ctx, cmd="echo test")
        
        assert "test output" in result
        mock_execute_command.assert_called_once_with("echo test", timeout=30)

    @pytest.mark.asyncio
    async def test_run_command_with_timeout(self, mock_execute_command):
        """Test run_command tool with custom timeout."""
        from termux_mcp.mcp_server_fastmcp import run_command
        
        mock_execute_command.return_value = (0, "output")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        
        result = run_command(mock_ctx, cmd="ls", timeout=60)
        
        assert "output" in result
        mock_execute_command.assert_called_once_with("ls", timeout=60)

    @pytest.mark.asyncio
    async def test_run_command_empty_returns_error(self):
        """Test run_command with empty cmd returns error."""
        from termux_mcp.mcp_server_fastmcp import run_command
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        
        result = run_command(mock_ctx, cmd="")
        
        assert "Error" in result or "error" in result

    @pytest.mark.asyncio
    async def test_get_battery_success(self, mock_execute_command):
        """Test get_battery tool executes termux-battery-status."""
        from termux_mcp.mcp_server_fastmcp import get_battery
        
        mock_execute_command.return_value = (0, '{"level": 100, "status": "CHARGING"}')
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = get_battery(mock_ctx)
        
        mock_execute_command.assert_called_once_with("termux-battery-status")
        assert "level" in result

    @pytest.mark.asyncio
    async def test_get_location_success(self, mock_execute_command):
        """Test get_location tool with default provider."""
        from termux_mcp.mcp_server_fastmcp import get_location
        
        mock_execute_command.return_value = (0, '{"latitude": 0.0, "longitude": 0.0}')
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = get_location(mock_ctx)
        
        mock_execute_command.assert_called_once_with("termux-location -p gps")
        assert "latitude" in result

    @pytest.mark.asyncio
    async def test_get_location_custom_provider(self, mock_execute_command):
        """Test get_location tool with custom provider."""
        from termux_mcp.mcp_server_fastmcp import get_location
        
        mock_execute_command.return_value = (0, '{"latitude": 0.0, "longitude": 0.0}')
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = get_location(mock_ctx, provider="network")
        
        mock_execute_command.assert_called_once_with("termux-location -p network")

    @pytest.mark.asyncio
    async def test_list_sms_success(self, mock_execute_command):
        """Test list_sms tool with limit parameter."""
        from termux_mcp.mcp_server_fastmcp import list_sms
        
        mock_execute_command.return_value = (0, "SMS message 1\nSMS message 2")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = list_sms(mock_ctx, limit=5)
        
        mock_execute_command.assert_called_once_with("termux-sms-list -l 5")

    @pytest.mark.asyncio
    async def test_get_clipboard_success(self, mock_execute_command):
        """Test get_clipboard tool."""
        from termux_mcp.mcp_server_fastmcp import get_clipboard
        
        mock_execute_command.return_value = (0, "clipboard content")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = get_clipboard(mock_ctx)
        
        mock_execute_command.assert_called_once_with("termux-clipboard-get")
        assert "clipboard content" in result

    @pytest.mark.asyncio
    async def test_set_clipboard_success(self, mock_execute_command):
        """Test set_clipboard tool."""
        from termux_mcp.mcp_server_fastmcp import set_clipboard
        
        mock_execute_command.return_value = (0, "")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = set_clipboard(mock_ctx, text="test text")
        
        mock_execute_command.assert_called_once()
        assert "successfully" in result.lower() or result == ""

    @pytest.mark.asyncio
    async def test_show_toast_success(self, mock_execute_command):
        """Test show_toast tool."""
        from termux_mcp.mcp_server_fastmcp import show_toast
        
        mock_execute_command.return_value = (0, "")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        
        result = show_toast(mock_ctx, message="Hello")
        
        mock_execute_command.assert_called_once()
        # Check that command starts with termux-toast
        call_args = mock_execute_command.call_args[0][0]
        assert call_args.startswith("termux-toast")

    @pytest.mark.asyncio
    async def test_get_wifi_info_success(self, mock_execute_command):
        """Test get_wifi_info tool."""
        from termux_mcp.mcp_server_fastmcp import get_wifi_info
        
        mock_execute_command.return_value = (0, '{"ssid": "TestNetwork"}')
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = get_wifi_info(mock_ctx)
        
        mock_execute_command.assert_called_once_with("termux-wifi-connectioninfo")
        assert "ssid" in result

    @pytest.mark.asyncio
    async def test_list_contacts_success(self, mock_execute_command):
        """Test list_contacts tool."""
        from termux_mcp.mcp_server_fastmcp import list_contacts
        
        mock_execute_command.return_value = (0, "Contact 1\nContact 2")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = list_contacts(mock_ctx)
        
        mock_execute_command.assert_called_once_with("termux-contact-list")

    @pytest.mark.asyncio
    async def test_get_device_info_success(self, mock_execute_command):
        """Test get_device_info tool."""
        from termux_mcp.mcp_server_fastmcp import get_device_info
        
        mock_execute_command.return_value = (0, '{"model": "TestDevice"}')
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.error = MagicMock()
        
        result = get_device_info(mock_ctx)
        
        mock_execute_command.assert_called_once_with("termux-info")
        assert "model" in result


class TestFastMcpErrorHandling:
    """Tests for FastMCP error handling."""

    @pytest.mark.asyncio
    async def test_command_failure_returns_output(self, mock_execute_command):
        """Test that non-zero exit code returns output with error info."""
        from termux_mcp.mcp_server_fastmcp import run_command
        
        mock_execute_command.return_value = (1, "Error output")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        mock_ctx.warning = MagicMock()
        
        result = run_command(mock_ctx, cmd="failing_cmd")
        
        # The output should contain the error
        assert "Error output" in result
        # Context warning should be called
        mock_ctx.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_execute_command):
        """Test that exceptions are handled gracefully."""
        from termux_mcp.mcp_server_fastmcp import run_command
        
        mock_execute_command.side_effect = RuntimeError("Command failed")
        
        mock_ctx = MagicMock()
        mock_ctx.info = MagicMock()
        
        # The function should raise the exception or handle it
        with pytest.raises(RuntimeError):
            run_command(mock_ctx, cmd="test")


class TestMCPProtocolCompliance:
    """Tests for MCP protocol compliance with FastMCP."""

    @pytest.mark.asyncio
    async def test_client_server_interaction(self, mcp_server, mock_execute_command):
        """Test basic client-server interaction using FastMCP Client."""
        mock_execute_command.return_value = (0, "test output")
        
        # Use FastMCP's client to test the server
        async with Client(mcp_server) as client:
            # Test tools/list
            tools = await client.list_tools()
            assert len(tools) == 10
            
            # Test tools/call
            result = await client.call_tool("run_command", {"cmd": "echo test"})
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
