"""Unit tests for termux_mcp.handler module.

Tests HTTP request handling, JSON parsing, and MCP protocol handling.
"""

import json
from unittest.mock import patch, MagicMock, call
import pytest

from termux_mcp.handler import MCPHandler
from termux_mcp.mcp_server import handle_mcp_request


class TestMCPHandlerAttributes:
    """Test MCPHandler class attributes."""

    def test_handler_is_http_handler(self):
        """Test that MCPHandler is a BaseHTTPRequestHandler."""
        from http.server import BaseHTTPRequestHandler
        assert issubclass(MCPHandler, BaseHTTPRequestHandler)

    def test_protocol_version(self):
        """Test protocol version attribute."""
        assert MCPHandler.protocol_version == "HTTP/1.1"


class TestReadJson:
    """Test _read_json method."""

    def test_read_valid_json(self):
        """Test reading valid JSON."""
        handler = MagicMock()
        body = {"test": "value"}
        body_bytes = json.dumps(body).encode("utf-8")
        handler.headers.get.return_value = str(len(body_bytes))
        handler.rfile.read.return_value = body_bytes
        
        result = MCPHandler._read_json(handler)
        assert result == body

    def test_read_empty_body(self):
        """Test reading empty body."""
        handler = MagicMock()
        handler.headers.get.return_value = "0"
        handler.rfile.read.return_value = b""
        
        result = MCPHandler._read_json(handler)
        assert result == {}

    def test_read_invalid_json(self):
        """Test reading invalid JSON."""
        handler = MagicMock()
        handler.headers.get.return_value = "10"
        handler.rfile.read.return_value = b"not json"
        
        result = MCPHandler._read_json(handler)
        assert result == {}

    def test_read_json_exception(self):
        """Test exception during JSON reading."""
        handler = MagicMock()
        handler.headers.get.side_effect = Exception("Test error")
        
        result = MCPHandler._read_json(handler)
        assert result == {}

    def test_read_json_zero_content_length(self):
        """Test reading with zero content length."""
        handler = MagicMock()
        handler.headers.get.return_value = "0"
        handler.rfile.read.return_value = b""
        
        result = MCPHandler._read_json(handler)
        assert result == {}


class TestJsonResponse:
    """Test _json_response method."""

    def test_json_response_structure(self):
        """Test JSON response format."""
        handler = MagicMock()
        handler.wfile = MagicMock()
        
        MCPHandler._json_response(handler, 200, {"status": "ok"})
        
        # Should call send_response, send_header, end_headers, write
        handler.send_response.assert_called_once_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")

    def test_json_response_body(self):
        """Test JSON response body content."""
        handler = MagicMock()
        handler.wfile = MagicMock()
        
        payload = {"test": "value"}
        MCPHandler._json_response(handler, 200, payload)
        
        # Check that body was written
        written_data = b""
        for call in handler.wfile.write.call_args_list:
            written_data += call[0][0]
        
        decoded = json.loads(written_data.decode("utf-8"))
        assert decoded == payload

    def test_json_response_sets_content_length(self):
        """Test that Content-Length is set correctly."""
        handler = MagicMock()
        handler.wfile = MagicMock()
        
        payload = {"test": "value"}
        MCPHandler._json_response(handler, 200, payload)
        
        # Check Content-Length header
        body = json.dumps(payload).encode("utf-8")
        handler.send_header.assert_any_call("Content-Length", str(len(body)))


class TestDoGet:
    """Test do_GET method."""

    def test_do_get_ping(self):
        """Test GET /ping endpoint."""
        handler = MagicMock()
        handler.path = "/ping"
        handler.wfile = MagicMock()
        
        MCPHandler.do_GET(handler)
        
        # Should call _json_response with 200
        handler._json_response.assert_called_once()
        call_args = handler._json_response.call_args
        assert call_args[0][0] == 200

    def test_do_get_ping_returns_json(self):
        """Test GET /ping returns JSON with status."""
        handler = MagicMock()
        handler.path = "/ping"
        handler.wfile = MagicMock()
        
        MCPHandler.do_GET(handler)
        
        # Check that _json_response was called with correct data
        handler._json_response.assert_called_once()
        call_args = handler._json_response.call_args
        response_data = call_args[0][1]
        assert "status" in response_data

    def test_do_get_not_found(self):
        """Test GET unknown path returns 404."""
        handler = MagicMock()
        handler.path = "/unknown"
        handler.wfile = MagicMock()
        
        MCPHandler.do_GET(handler)
        
        handler._json_response.assert_called_once()
        call_args = handler._json_response.call_args
        assert call_args[0][0] == 404


class TestDoPost:
    """Test do_POST method."""

    def test_do_post_mcp_initialize(self):
        """Test POST /mcp with initialize method."""
        handler = MagicMock()
        handler.path = "/mcp"
        handler.wfile = MagicMock()
        
        # Setup _read_json to return the request body
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        handler._read_json.return_value = body
        
        MCPHandler.do_POST(handler)
        
        # Should call _json_response with 200
        handler._json_response.assert_called_once()
        call_args = handler._json_response.call_args
        assert call_args[0][0] == 200

    def test_do_post_run(self):
        """Test POST /run endpoint."""
        handler = MagicMock()
        handler.path = "/run"
        handler.wfile = MagicMock()
        
        # Setup _read_json to return the request body
        body = {"cmd": "echo test", "timeout": 30}
        handler._read_json.return_value = body
        
        with patch("termux_mcp.handler.execute_streaming"):
            MCPHandler.do_POST(handler)
            # Should have called execute_streaming
            from termux_mcp.handler import execute_streaming
            execute_streaming.assert_called_once()

    def test_do_post_run_missing_cmd(self):
        """Test POST /run with missing cmd."""
        handler = MagicMock()
        handler.path = "/run"
        handler.wfile = MagicMock()
        
        # Setup _read_json to return empty body
        handler._read_json.return_value = {}
        
        MCPHandler.do_POST(handler)
        
        # Should return 400 error
        handler._json_response.assert_called_once()
        call_args = handler._json_response.call_args
        assert call_args[0][0] == 400

    def test_do_post_mcp_notification(self):
        """Test POST /mcp with notification (no response body)."""
        handler = MagicMock()
        handler.path = "/mcp"
        handler.wfile = MagicMock()
        
        # Setup _read_json to return the notification body
        notification_body = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        handler._read_json.return_value = notification_body
        
        MCPHandler.do_POST(handler)
        
        # Should send 204 No Content
        handler.send_response.assert_called_once_with(204)

    def test_do_post_not_found(self):
        """Test POST to unknown path."""
        handler = MagicMock()
        handler.path = "/unknown"
        handler.wfile = MagicMock()
        
        MCPHandler.do_POST(handler)
        
        handler._json_response.assert_called_once()
        call_args = handler._json_response.call_args
        assert call_args[0][0] == 404


class TestHandlerIntegration:
    """Integration tests for handler with mcp_server."""

    def test_full_mcp_initialize_flow(self):
        """Test complete MCP initialize via handler."""
        handler = MagicMock()
        handler.path = "/mcp"
        handler.wfile = MagicMock()
        
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        body_bytes = json.dumps(body).encode("utf-8")
        handler.headers.get.return_value = str(len(body_bytes))
        handler.rfile.read.return_value = body_bytes
        
        MCPHandler.do_POST(handler)
        
        # Check response - should have written JSON
        written_data = b""
        for call in handler.wfile.write.call_args_list:
            written_data += call[0][0]
        
        if written_data:
            decoded = json.loads(written_data.decode("utf-8"))
            assert "result" in decoded or "error" in decoded

    def test_full_mcp_tools_list(self):
        """Test complete MCP tools/list via handler."""
        handler = MagicMock()
        handler.path = "/mcp"
        handler.wfile = MagicMock()
        
        body = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        body_bytes = json.dumps(body).encode("utf-8")
        handler.headers.get.return_value = str(len(body_bytes))
        handler.rfile.read.return_value = body_bytes
        
        MCPHandler.do_POST(handler)
        
        # Check response contains tools
        written_data = b""
        for call in handler.wfile.write.call_args_list:
            written_data += call[0][0]
        
        if written_data:
            decoded = json.loads(written_data.decode("utf-8"))
            assert "tools" in decoded.get("result", {})
