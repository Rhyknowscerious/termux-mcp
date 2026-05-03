#!/bin/bash
# termux-mcp Deployment Script
# Run this on the Termux device

set -e

echo "=== Termux-MCP Deployment ==="

# 1. Stop any existing termux_mcp server
echo "[1/4] Stopping existing server..."
pkill -f "python.*termux_mcp" 2>/dev/null || true
pkill -f "python.*mcp_server" 2>/dev/null || true
sleep 1

# 2. Update code (if git is available)
if [ -d ".git" ]; then
    echo "[2/4] Updating from git..."
    git pull 2>/dev/null || echo "  (git pull skipped - no remote or clean)"
else
    echo "[2/4] No git repo found - assuming fresh deployment"
fi

# 3. Start termux-mcp on port 8000 (ACTIVE)
echo "[3/4] Starting termux-mcp on port 8000..."
export TERMUX_MCP_PORT=8000
python -m termux_mcp &
sleep 2

# 4. Verify
echo "[4/4] Verifying server..."
if curl -s http://localhost:8000/mcp > /dev/null 2>&1; then
    echo "✅ termux-mcp running on http://localhost:8000"
    echo "   Tools available at http://localhost:8000/mcp"
else
    echo "❌ Server failed to start - check logs"
    exit 1
fi

echo ""
echo "=== Deployment Complete ==="
echo "Active: termux-mcp on port 8000"
echo ""
