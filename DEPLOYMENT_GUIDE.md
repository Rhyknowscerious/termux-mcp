# Termux MCP - FastMCP Migration Deployment Guide

## For Termux Agent Team

This guide walks through deploying the new FastMCP-based termux-mcp server on the Termux device.

---

## Pre-Deployment Checklist

- [ ] Backup any local changes (if modifying an existing installation)
- [ ] Ensure Python 3.8+ is installed: `python --version`
- [ ] Ensure pip is available: `pip --version` or `python -m pip --version`

---

## Step 1: Update the Repository

```bash
# Navigate to the termux-mcp directory
cd ~/git.repos/bitbucket/rhyknowscerious/termux-mcp
# or wherever the repo is cloned

# Switch to the refactor branch
git fetch origin
git checkout refactor
git pull origin refactor
```

---

## Step 2: Install Dependencies

```bash
# Option A: Using virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate
pip install fastmcp
pip install -r requirements.txt

# Option B: System-wide (if venv not available)
pip install fastmcp
pip install -r requirements.txt
```

---

## Step 3: Stop the Old Server

```bash
# Stop any running termux-mcp server
pkill -f "python.*termux_mcp" 2>/dev/null || true
pkill -f "python.*mcp_server" 2>/dev/null || true
sleep 2
```

---

## Step 4: Start the New FastMCP Server

```bash
# Using the default port (8000)
python -m termux_mcp

# Or with custom port
TERMUX_MCP_PORT=8000 python -m termux_mcp

# Or if using virtual environment
source .venv/bin/activate
python -m termux_mcp
```

The server should start and show:
```
🚀 Starting TermuxMCP (FastMCP) on 0.0.0.0:8000
📂 Working dir: /data/data/com.termux/files/home
Press Ctrl+C to stop.

FastMCP 3.2.4
Server: termux-mcp, 2.0.0
```

---

## Step 5: Verify the Deployment

### Test the health endpoint:
```bash
curl http://localhost:8000/ping
```
Expected response:
```json
{"status": "ok", "cwd": "/data/data/com.termux/files/home", "server": "termux-mcp-fastmcp", "version": "2.0.0"}
```

### Test the MCP endpoint:
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```
Expected: JSON response with list of 10 tools.

### Run the integration test script:
```bash
python test_integration.py
```

---

## Available Tools (10 Total)

| Tool | Description |
|------|-------------|
| `run_command` | Execute shell commands |
| `get_battery` | Get battery status |
| `get_location` | Get GPS location |
| `list_sms` | List SMS messages |
| `get_clipboard` | Get clipboard content |
| `set_clipboard` | Set clipboard content |
| `show_toast` | Show toast notification |
| `get_wifi_info` | Get WiFi info |
| `list_contacts` | List contacts |
| `get_device_info` | Get device info |

---

## Integration Testing with AI Agents

### Using with Claude Desktop

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "termux": {
      "url": "http://192.168.0.128:8000/mcp"
    }
  }
}
```

### Using with MCP CLI Tools

```bash
# List tools
mcp call http://192.168.0.128:8000/mcp tools/list

# Call a tool
mcp call http://192.168.0.128:8000/mcp tools/call run_command '{"cmd":"ls -la"}'
```

---

## Rollback (If Needed)

If issues are encountered, you can switch back to the old implementation:

```bash
# Switch to main branch (old implementation)
git checkout main
pkill -f "python.*termux_mcp"
python -m termux_mcp
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
netstat -tulpn | grep 8000
# Or
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### FastMCP Not Found
```bash
# Reinstall fastmcp
pip install --force-reinstall fastmcp

# Verify installation
python -c "import fastmcp; print(fastmcp.__version__)"
```

### Server Starts but Tools Not Available
```bash
# Check server logs
tail -f termux-mcp.log  # if using nohup

# Test directly
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' -v
```

---

## Next Steps

1. **Test all 10 tools** to ensure they work on the actual Termux device
2. **Test with an AI agent** (Claude, etc.) to verify MCP compliance
3. **Report any issues** encountered during testing
4. **Performance testing** - compare response times with old implementation

---

## Contact

For issues or questions:
- GitHub: https://github.com/Rhyknowscerious/termux-mcp
- Branch: `refactor`
- Commit: Latest on `origin/refactor`

---

**Happy Testing! 🚀**
