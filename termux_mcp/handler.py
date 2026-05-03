"""
Termux MCP Server - HTTP Handler (Backward Compatibility)

This module provides HTTP handlers for backward compatibility with the old API.
For new implementations, use the FastMCP server directly via server.py.

This handler supports:
- GET /ping - Health check
- POST /run - Execute commands with streaming output
- POST /mcp - MCP protocol endpoint (delegates to FastMCP)
"""

import json
import logging
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

from .mcp_server_fastmcp import mcp
from .shell import execute_streaming, get_current_dir

logger = logging.getLogger(__name__)


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP handler for TermuxMCP server with FastMCP backend."""
    
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        logger.debug("[HTTP] " + fmt, *args)

    def _log(self, msg: str):
        logger.info(f"[MCP] {msg}")

    def _read_json(self) -> dict:
        """Read and parse JSON from request body."""
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            self._log(f"Request body: {raw}")
            if not raw:
                return {}
            return json.loads(raw)
        except Exception as e:
            self._log(f"JSON read error: {e}")
            return {}

    def _json_response(self, status: int, payload: dict) -> None:
        """Send a JSON response."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        """Handle GET requests."""
        path = urlparse(self.path).path
        self._log(f"GET {path}")

        if path == "/ping":
            self._json_response(200, {
                "status": "ok",
                "cwd": get_current_dir(),
                "server": "termux-mcp-fastmcp",
                "version": "2.0.0",
            })
            return

        self._json_response(404, {"error": "Not found"})

    def do_POST(self) -> None:
        """Handle POST requests."""
        path = urlparse(self.path).path
        self._log(f"POST {path}")

        data = self._read_json()
        self._log(f"Parsed JSON: {data}")

        # Legacy /run endpoint for streaming command execution
        if path == "/run":
            cmd = data.get("cmd", "").strip()
            timeout = data.get("timeout", 30)
            if not cmd:
                self._json_response(400, {"error": "Missing 'cmd'"})
                return
            self._log(f"Executing: {cmd} (timeout: {timeout}s)")
            execute_streaming(self, cmd, timeout=timeout)
            return

        # Legacy /mcp endpoint - redirect to FastMCP
        if path == "/mcp":
            self._log(f"MCP method: {data.get('method')}")
            # For now, return a message directing to use FastMCP directly
            self._json_response(200, {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "message": "Please use FastMCP HTTP transport directly",
                    "server": "termux-mcp-fastmcp"
                }
            })
            return

        self._json_response(404, {"error": "Not found"})
