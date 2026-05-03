<div align="center">
<a href="https://play.google.com/store/apps/details?id=com.codeninja.termuxtutor"><img src="https://raw.githubusercontent.com/Bhai4You/bhai4you/refs/heads/master/termux-mcp.png" alt="Termux Tutor"  ></a>
    

A lightweight HTTP server that exposes Termux Shell as an MCP (Model Context Protocol) server —
built to pair with AI agents, Claude, or any MCP-compatible client.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
![Platform](https://img.shields.io/badge/Platform-Termux%20%7C%20Android-green?style=flat-square&logo=android)](https://termux.dev)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()
![FastMCP](https://img.shields.io/badge/FastMCP-3.2+-red?style=flat-square)]()

</div>

---

## 📖 What is TermuxMCP?

TermuxMCP runs inside [Termux](https://termux.dev) and provides an MCP (Model Context Protocol) interface so any AI agent can:

- 🖥️ Execute shell commands via `run_command` tool
- 📱 Access device features: battery, location, WiFi, contacts, SMS
- 📋 Manage clipboard (get/set)
- 🔔 Show toast notifications
- 📂 Navigate directories with **persistent `cd` state**
- 📦 Install packages **non-interactively** (`pkg install`, `apt install`)

**Now powered by [FastMCP](https://github.com/jlowin/fastmcp)** - a modern, clean MCP server framework!

```
AI Agent ──► MCP Protocol ──► TermuxMCP (FastMCP) ──► Termux Shell
                    │
                    └── 10 Tools: run_command, get_battery, get_location, ...
```

---

## Quick Start

### 1 — Install in Termux

```bash
pkg update && pkg install python git -y
git clone https://github.com/termuxgpt/termux-mcp
cd termux-mcp
python -m termux_mcp
```

### Or use the automated installer (recommended)
```bash
curl -L https://termux-mcp.pages.dev/add-repo.sh | bash
pkg install termux-mcp
termux-mcp
```

### 2 — Test it

```bash
# Health check
curl http://localhost:8000/ping

# List available MCP tools (using an MCP client)
# The server provides 10 tools via the MCP protocol at /mcp endpoint

# For legacy support, you can still use:
curl -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"cmd": "ls ~"}'
```

### 3 — Custom port

```bash
TERMUX_MCP_PORT=9090 python -m termux_mcp
```

---

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `run_command` | Execute a shell command on the Termux device |
| `get_battery` | Get battery status using termux-battery-status |
| `get_location` | Get GPS location using termux-location |
| `list_sms` | List SMS messages using termux-sms-list |
| `get_clipboard` | Get clipboard content using termux-clipboard-get |
| `set_clipboard` | Set clipboard content using termux-clipboard-set |
| `show_toast` | Show a toast notification using termux-toast |
| `get_wifi_info` | Get WiFi connection info using termux-wifi-connectioninfo |
| `list_contacts` | List contacts using termux-contact-list |
| `get_device_info` | Get device info using termux-info |

---

## API Reference

### MCP Endpoint (Primary)
- **URL**: `http://localhost:8000/mcp`
- **Protocol**: MCP (Model Context Protocol)
- **Transport**: HTTP (Streamable HTTP)

### Legacy Endpoints (Backward Compatibility)
| Method | Path    | Body                   | Response                       |
|--------|---------|------------------------|--------------------------------|
| GET    | `/ping` | —                      | `{"status":"ok","cwd":"..."}` |
| POST   | `/run`  | `{"cmd": "<shell>"}` | Chunked plain-text stream      |

### Streaming Response Format (Legacy /run endpoint)
Output uses HTTP chunked transfer encoding (`Transfer-Encoding: chunked`).  
Read it line by line — each line is real terminal output **as it happens**.

---

## Configuration

All settings can be overridden via environment variables:

| Variable              | Default     | Description                   |
|-----------------------|-------------|--------------------------------|
| `TERMUX_MCP_PORT`     | `8000`      | HTTP listen port               |
| `TERMUX_MCP_HOST`     | `0.0.0.0`  | Bind address                   |
| `HOME`                | Termux home | Working directory base         |

---

## Migrating from Old Version

This version uses **FastMCP** instead of a custom MCP implementation. Key changes:

1. **MCP Endpoint**: Now uses FastMCP's HTTP transport at `/mcp`
2. **Tool Definitions**: Defined using `@mcp.tool()` decorators
3. **Type Validation**: Uses Pydantic for input validation
4. **Context Support**: Tools can access MCP context for logging, progress, etc.

For legacy support, the old `/run` and `/ping` endpoints are still available.

---

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
python -m pytest tests/ -v

# Run only FastMCP tests
python -m pytest tests/test_fastmcp_server.py -v
```

### Project Structure

```
termux-mcp/
├── termux_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── mcp_server_fastmcp.py  # New FastMCP implementation
│   ├── mcp_server.py           # Old implementation (deprecated)
│   ├── server.py               # Server entry point
│   ├── shell.py                # Command execution
│   └── ...
├── tests/
│   ├── test_fastmcp_server.py  # New FastMCP tests
│   └── ...
├── requirements.txt
└── README.md
```

---

## License

MIT License - See LICENSE file for details.
