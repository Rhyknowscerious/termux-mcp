"""Unit tests for termux-mcp server.

These tests verify the MCP protocol handlers, JSON-RPC request/response handling,
and error handling for unknown tools. The shell.execute_command is mocked to test
tool handlers without actually executing commands.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from termux_mcp.mcp_server import (
    MCP_VERSION,
    TOOLS,
    handle_initialize,
    handle_tools_list,
    handle_tools_call,
    handle_mcp_request,
)


# Test fixtures

@pytest.fixture
def mock_execute_command():
    """Mock execute_command for testing tool handlers."""
    with patch("termux_mcp.mcp_server.execute_command") as mock:
        yield mock


class TestInitialize:
    """Tests for MCP initialize protocol handler."""

    def test_initialize_returns_protocol_version(self):
        """Test that initialize returns the correct protocol version."""
        result = handle_initialize({})
        
        assert result["protocolVersion"] == MCP_VERSION

    def test_initialize_returns_capabilities(self):
        """Test that initialize returns server capabilities."""
        result = handle_initialize({})
        
        assert "capabilities" in result
        assert "tools" in result["capabilities"]

    def test_initialize_returns_server_info(self):
        """Test that initialize returns server info."""
        result = handle_initialize({})
        
        assert "serverInfo" in result
        assert result["serverInfo"]["name"] == "termux-mcp"
        assert result["serverInfo"]["version"] == "1.0.0"

    def test_initialize_accepts_params(self):
        """Test that initialize accepts parameters without error."""
        result = handle_initialize({"protocolVersion": "test"})
        
        assert "protocolVersion" in result


class TestToolsList:
    """Tests for MCP tools/list protocol handler."""

    def test_tools_list_returns_tools_array(self):
        """Test that tools/list returns array of tools."""
        result = handle_tools_list({})
        
        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) > 0

    def test_tools_list_contains_all_tools(self):
        """Test that tools list contains all expected tools."""
        result = handle_tools_list({})
        tool_names = {tool["name"] for tool in result["tools"]}
        
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
        assert expected_tools == tool_names

    def test_tool_has_name_and_description(self):
        """Test that each tool has required name and description."""
        result = handle_tools_list({})
        
        for tool in result["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    def test_run_command_tool_schema(self):
        """Test run_command tool has correct input schema."""
        result = handle_tools_list({})
        run_command = next(t for t in result["tools"] if t["name"] == "run_command")
        
        assert "cmd" in run_command["inputSchema"]["properties"]
        assert "timeout" in run_command["inputSchema"]["properties"]
        assert run_command["inputSchema"]["required"] == ["cmd"]

    def test_list_sms_tool_schema(self):
        """Test list_sms tool has correct input schema."""
        result = handle_tools_list({})
        list_sms = next(t for t in result["tools"] if t["name"] == "list_sms")
        
        assert "limit" in list_sms["inputSchema"]["properties"]
        assert list_sms["inputSchema"]["properties"]["limit"]["default"] == 10


class TestToolsCall:
    """Tests for MCP tools/call protocol handler."""

    def test_run_command_success(self, mock_execute_command):
        """Test run_command tool executes command successfully."""
        mock_execute_command.return_value = (0, "test output")
        
        result = handle_tools_call({
            "name": "run_command",
            "arguments": {"cmd": "echo test"}
        })
        
        assert "content" in result
        assert result["content"][0]["text"] == "test output"
        assert result["isError"] is False
        mock_execute_command.assert_called_once_with("echo test")

    def test_run_command_empty_cmd_returns_error(self):
        """Test run_command with empty cmd returns error."""
        result = handle_tools_call({
            "name": "run_command",
            "arguments": {}
        })
        
        assert result["isError"] is True
        assert "Error" in result["content"][0]["text"]

    def test_run_command_with_timeout(self, mock_execute_command):
        """Test run_command tool accepts timeout parameter."""
        mock_execute_command.return_value = (0, "output")
        
        result = handle_tools_call({
            "name": "run_command",
            "arguments": {"cmd": "ls", "timeout": 60}
        })
        
        assert "content" in result

    def test_get_battery_success(self, mock_execute_command):
        """Test get_battery tool executes termux-battery-status."""
        mock_execute_command.return_value = (0, '{"level": 100, "status": "CHARGING"}')
        
        result = handle_tools_call({
            "name": "get_battery",
            "arguments": {}
        })
        
        mock_execute_command.assert_called_once_with("termux-battery-status")
        assert result["isError"] is False

    def test_get_location_success(self, mock_execute_command):
        """Test get_location tool with default provider."""
        mock_execute_command.return_value = (0, '{"latitude": 0.0, "longitude": 0.0}')
        
        result = handle_tools_call({
            "name": "get_location",
            "arguments": {}
        })
        
        mock_execute_command.assert_called_once_with("termux-location -p gps")
        assert result["isError"] is False

    def test_get_location_custom_provider(self, mock_execute_command):
        """Test get_location tool with custom provider."""
        mock_execute_command.return_value = (0, '{"latitude": 0.0, "longitude": 0.0}')
        
        result = handle_tools_call({
            "name": "get_location",
            "arguments": {"provider": "network"}
        })
        
        mock_execute_command.assert_called_once_with("termux-location -p network")

    def test_list_sms_success(self, mock_execute_command):
        """Test list_sms tool with limit parameter."""
        mock_execute_command.return_value = (0, "SMS message 1\nSMS message 2")
        
        result = handle_tools_call({
            "name": "list_sms",
            "arguments": {"limit": 5}
        })
        
        mock_execute_command.assert_called_once_with("termux-sms-list -l 5")
        assert result["isError"] is False

    def test_get_clipboard_success(self, mock_execute_command):
        """Test get_clipboard tool."""
        mock_execute_command.return_value = (0, "clipboard content")
        
        result = handle_tools_call({
            "name": "get_clipboard",
            "arguments": {}
        })
        
        mock_execute_command.assert_called_once_with("termux-clipboard-get")

    def test_set_clipboard_success(self, mock_execute_command):
        """Test set_clipboard tool."""
        mock_execute_command.return_value = (0, "")
        
        result = handle_tools_call({
            "name": "set_clipboard",
            "arguments": {"text": "test text"}
        })
        
        mock_execute_command.assert_called_once_with("termux-clipboard-set 'test text'")
        assert result["isError"] is False

    def test_show_toast_success(self, mock_execute_command):
        """Test show_toast tool."""
        mock_execute_command.return_value = (0, "")

        result = handle_tools_call({
            "name": "show_toast",
            "arguments": {"message": "Hello"}
        })

        # Check that command starts with termux-toast (shlex.quote adds quotes)
        call_args = mock_execute_command.call_args[0][0]
        assert call_args.startswith("termux-toast")
        assert result["isError"] is False

    def test_get_wifi_info_success(self, mock_execute_command):
        """Test get_wifi_info tool."""
        mock_execute_command.return_value = (0, '{"ssid": "TestNetwork"}')
        
        result = handle_tools_call({
            "name": "get_wifi_info",
            "arguments": {}
        })
        
        mock_execute_command.assert_called_once_with("termux-wifi-connectioninfo")

    def test_list_contacts_success(self, mock_execute_command):
        """Test list_contacts tool."""
        mock_execute_command.return_value = (0, "Contact 1\nContact 2")
        
        result = handle_tools_call({
            "name": "list_contacts",
            "arguments": {}
        })
        
        mock_execute_command.assert_called_once_with("termux-contact-list")

    def test_get_device_info_success(self, mock_execute_command):
        """Test get_device_info tool."""
        mock_execute_command.return_value = (0, '{"model": "TestDevice"}')
        
        result = handle_tools_call({
            "name": "get_device_info",
            "arguments": {}
        })
        
        mock_execute_command.assert_called_once_with("termux-info")

    def test_unknown_tool_returns_error(self, mock_execute_command):
        """Test unknown tool returns error."""
        result = handle_tools_call({
            "name": "unknown_tool",
            "arguments": {}
        })
        
        assert result["isError"] is True
        assert "Unknown tool" in result["content"][0]["text"]

    def test_tool_exception_handling(self, mock_execute_command):
        """Test that tool exceptions are caught and returned as error."""
        mock_execute_command.side_effect = RuntimeError("Command failed")
        
        result = handle_tools_call({
            "name": "run_command",
            "arguments": {"cmd": "test"}
        })
        
        assert result["isError"] is True
        assert "Error" in result["content"][0]["text"]
        assert "Command failed" in result["content"][0]["text"]

    def test_exit_code_non_zero_is_error(self, mock_execute_command):
        """Test that non-zero exit code marks result as error."""
        mock_execute_command.return_value = (1, "Error output")
        
        result = handle_tools_call({
            "name": "run_command",
            "arguments": {"cmd": "failing_cmd"}
        })
        
        assert result["isError"] is True


class TestJsonRpcRequest:
    """Tests for JSON-RPC request/response handling."""

    def test_initialize_request(self):
        """Test JSON-RPC initialize request."""
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "result" in result
        assert result["result"]["protocolVersion"] == MCP_VERSION

    def test_tools_list_request(self):
        """Test JSON-RPC tools/list request."""
        body = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 2
        assert "result" in result
        assert "tools" in result["result"]

    def test_tools_call_request(self, mock_execute_command):
        """Test JSON-RPC tools/call request."""
        mock_execute_command.return_value = (0, "output")
        
        body = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "run_command",
                "arguments": {"cmd": "echo test"}
            }
        }
        
        result = handle_mcp_request(body)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 3
        assert "result" in result
        assert "content" in result["result"]

    def test_notifications_initialized_returns_none(self):
        """Test notifications/initialized returns None (no response)."""
        body = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "notifications/initialized",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert result is None

    def test_unknown_method_returns_error(self):
        """Test unknown method returns error response."""
        body = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "unknown/method",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert "error" in result
        assert result["error"]["code"] == -32601
        assert "Method not found" in result["error"]["message"]

    def test_request_without_id(self):
        """Test request without id field."""
        body = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert "id" in result
        assert result["id"] is None

    def test_request_with_null_id(self):
        """Test request with null id field."""
        body = {
            "jsonrpc": "2.0",
            "id": None,
            "method": "tools/list",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert result["id"] is None


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_missing_tool_name_returns_error(self, mock_execute_command):
        """Test missing tool name returns error."""
        result = handle_tools_call({
            "name": "",
            "arguments": {}
        })
        
        assert result["isError"] is True

    def test_exception_in_handler_returns_error(self):
        """Test exception in handler returns JSON-RPC error."""
        with patch("termux_mcp.mcp_server.handle_tools_call") as mock:
            mock.side_effect = Exception("Test error")
            
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "test", "arguments": {}}
            }
            
            result = handle_mcp_request(body)
            
            assert "error" in result
            assert result["error"]["code"] == -32603

    def test_empty_arguments_handled(self, mock_execute_command):
        """Test empty arguments are handled gracefully."""
        mock_execute_command.return_value = (0, "output")
        
        result = handle_tools_call({
            "name": "get_battery",
            "arguments": None
        })
        
        assert "content" in result


class TestMcpProtocol:
    """Tests for MCP protocol compliance."""

    def test_jsonrpc_version_20(self):
        """Test responses use JSON-RPC 2.0."""
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        result = handle_mcp_request(body)
        
        assert result["jsonrpc"] == "2.0"

    def test_protocol_version_format(self):
        """Test protocol version format."""
        assert MCP_VERSION == "2025-11-25"

    def test_tools_call_response_format(self, mock_execute_command):
        """Test tools/call response has correct format."""
        mock_execute_command.return_value = (0, "output")
        
        result = handle_tools_call({
            "name": "run_command",
            "arguments": {"cmd": "test"}
        })
        
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"
        assert "text" in result["content"][0]
        assert "isError" in result


class TestIntegration:
    """Integration tests for complete request/response cycles."""

    def test_full_initialize_flow(self):
        """Test complete initialize flow."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        result = handle_mcp_request(request)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert "result" in result
        result_data = result["result"]
        assert result_data["protocolVersion"] == MCP_VERSION
        assert "capabilities" in result_data
        assert "serverInfo" in result_data

    def test_full_tools_list_flow(self):
        """Test complete tools/list flow."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        result = handle_mcp_request(request)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 2
        assert len(result["result"]["tools"]) == 10

    def test_full_tool_execution_flow(self, mock_execute_command):
        """Test complete tool execution flow."""
        mock_execute_command.return_value = (0, "Battery: 100%")
        
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_battery",
                "arguments": {}
            }
        }
        
        result = handle_mcp_request(request)
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 3
        assert result["result"]["content"][0]["text"] == "Battery: 100%"
        assert result["result"]["isError"] is False

    def test_error_flow_unknown_tool(self, mock_execute_command):
        """Test error flow for unknown tool."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "non_existent_tool",
                "arguments": {}
            }
        }
        
        result = handle_mcp_request(request)
        
        assert result["result"]["isError"] is True
        assert "Unknown tool" in result["result"]["content"][0]["text"]