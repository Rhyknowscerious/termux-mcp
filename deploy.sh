#!/bin/bash
# termux-mcp Deployment Script (FastMCP Version)
# Run this on the Termux device

set -e

echo "=== Termux-MCP Deployment (FastMCP) ==="

# 1. Stop any existing termux_mcp server
echo "[1/5] Stopping existing server..."
pkill -f "python.*termux_mcp" 2>/dev/null || true
pkill -f "python.*mcp_server" 2>/dev/null || true
sleep 1

# 2. Update code (if git is available)
if [ -d ".git" ]; then
    echo "[2/5] Updating from git..."
    git pull 2>/dev/null || echo "  (git pull skipped - no remote or clean)"
else
    echo "[2/5] No git repo found - assuming fresh deployment"
fi

# 3. Install/update dependencies
echo "[3/5] Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt 2>/dev/null || python -m pip install -r requirements.txt
elif [ -d ".venv" ]; then
    echo "  Using existing virtual environment"
else
    echo "  Creating virtual environment..."
    python -m venv .venv
fi

# Install fastmcp if not already installed
python -c "import fastmcp" 2>/dev/null || {
    echo "  Installing fastmcp..."
    pip install fastmcp || python -m pip install fastmcp
}

# 4. Start termux-mcp on port 8000 (ACTIVE)
echo "[4/5] Starting termux-mcp (FastMCP) on port 8000..."
export TERMUX_MCP_PORT=8000
nohup python -m termux_mcp > termux-mcp.log 2>&1 &
sleep 3

# 5. Verify
echo "[5/5] Verifying server..."
if curl -s http://localhost:8000/ping > /dev/null 2>&1; then
    echo "✅ termux-mcp (FastMCP) running on http://localhost:8000"
    echo "   Health check: http://localhost:8000/ping"
    echo "   MCP endpoint: http://localhost:8000/mcp"
elif curl -s http://localhost:8000/mcp > /dev/null 2>&1; then
    echo "✅ termux-mcp (FastMCP) running on http://localhost:8000"
    echo "   MCP endpoint available"
else
    echo "❌ Server failed to start - check termux-mcp.log"
    tail -20 termux-mcp.log 2>/dev/null || true
    exit 1
fi

echo ""
echo "=== Deployment Complete ==="
echo "Server: termux-mcp (FastMCP)"
echo "Port: 8000"
echo "Log: termux-mcp.log"
echo ""
echo "To view logs: tail -f termux-mcp.log"
echo "To stop: pkill -f 'python.*termux_mcp'"
