import json
import logging
import shlex
from typing import Any

from .shell import execute_command, get_current_dir

logger = logging.getLogger(__name__)

# MCP protocol version
MCP_VERSION = "2025-05-03"

# Tool definitions mapping to termux commands
TOOLS = [
    {
        "name": "run_command",
        "description": "Execute a shell command on the Termux device",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cmd": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            "required": ["cmd"]
        }
    },
    {
        "name": "get_battery",
        "description": "Get battery status using termux-battery-status",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_location",
        "description": "Get GPS location using termux-location",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Location provider: gps, network, passive",
                    "default": "gps"
                }
            }
        }
    },
    {
        "name": "list_sms",
        "description": "List SMS messages using termux-sms-list",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to return",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_clipboard",
        "description": "Get clipboard content using termux-clipboard-get",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "set_clipboard",
        "description": "Set clipboard content using termux-clipboard-set",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to copy to clipboard"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "show_toast",
        "description": "Show a toast notification using termux-toast",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to display in toast"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_wifi_info",
        "description": "Get WiFi connection info using termux-wifi-connectioninfo",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_contacts",
        "description": "List contacts using termux-contact-list",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_device_info",
        "description": "Get device info using termux-info",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def handle_initialize(params: dict) -> dict:
    """Handle MCP initialize request."""
    return {
        "protocolVersion": MCP_VERSION,
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "termux-mcp2",
            "version": "2.0.0"
        }
    }


def handle_tools_list(params: dict) -> dict:
    """Handle tools/list request."""
    return {
        "tools": TOOLS
    }


def handle_tools_call(params: dict) -> dict:
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "run_command":
            cmd = arguments.get("cmd", "")
            if not cmd:
                return {
                    "content": [{"type": "text", "text": "Error: No command provided"}],
                    "isError": True
                }
            exit_code, output = execute_command(cmd)
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "get_battery":
            exit_code, output = execute_command("termux-battery-status")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "get_location":
            provider = arguments.get("provider", "gps")
            exit_code, output = execute_command(f"termux-location -p {shlex.quote(provider)}")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "list_sms":
            limit = arguments.get("limit", 10)
            exit_code, output = execute_command(f"termux-sms-list -l {shlex.quote(str(limit))}")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "get_clipboard":
            exit_code, output = execute_command("termux-clipboard-get")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "set_clipboard":
            text = arguments.get("text", "")
            exit_code, output = execute_command(f"termux-clipboard-set {shlex.quote(text)}")
            return {
                "content": [{"type": "text", "text": output or "Clipboard set successfully"}],
                "isError": exit_code != 0
            }

        elif tool_name == "show_toast":
            message = arguments.get("message", "")
            exit_code, output = execute_command(f"termux-toast {shlex.quote(message)}")
            return {
                "content": [{"type": "text", "text": output or "Toast shown"}],
                "isError": exit_code != 0
            }

        elif tool_name == "get_wifi_info":
            exit_code, output = execute_command("termux-wifi-connectioninfo")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "list_contacts":
            exit_code, output = execute_command("termux-contact-list")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        elif tool_name == "get_device_info":
            exit_code, output = execute_command("termux-info")
            return {
                "content": [{"type": "text", "text": output}],
                "isError": exit_code != 0
            }

        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }
    except Exception as e:
        logger.error(f"Error handling tool {tool_name}: {e}")
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


def handle_mcp_request(body: dict) -> dict:
    """Handle MCP JSON-RPC request and return response dict."""
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    try:
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "tools/list":
            result = handle_tools_list(params)
        elif method == "tools/call":
            result = handle_tools_call(params)
        elif method == "notifications/initialized":
            # Client confirmed initialization - no response needed
            return None
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    except Exception as e:
        logger.error(f"MCP error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
