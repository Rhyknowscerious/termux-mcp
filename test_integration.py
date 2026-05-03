#!/usr/bin/env python
"""
Termux MCP FastMCP - Integration Test Script

This script tests the FastMCP-based Termux MCP server to ensure:
1. Server starts correctly
2. All 10 tools are available
3. Tools can be called and return expected results

Run this on the Termux device after deployment.
"""

import json
import sys
import time
import subprocess
import requests
from contextlib import contextmanager

# Test configuration
SERVER_URL = "http://localhost:8000"
TIMEOUT = 5


@contextmanager
def start_server():
    """Start the termux-mcp server for testing."""
    print("Starting termux-mcp server...")
    proc = subprocess.Popen(
        ["python", "-m", "termux_mcp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # Wait for server to start
    time.sleep(3)
    try:
        yield proc
    finally:
        print("Stopping server...")
        proc.terminate()
        proc.wait(timeout=5)


def test_ping():
    """Test the /ping endpoint."""
    print("\n[TEST] Health check (/ping)")
    try:
        resp = requests.get(f"{SERVER_URL}/ping", timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  ✅ PASSED - Status: {data.get('status')}")
            print(f"     Working dir: {data.get('cwd')}")
            return True
        else:
            print(f"  ❌ FAILED - Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED - Error: {e}")
        return False


def test_mcp_endpoint():
    """Test the MCP endpoint with a tools/list request."""
    print("\n[TEST] MCP endpoint (/mcp) - tools/list")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        resp = requests.post(
            f"{SERVER_URL}/mcp",
            json=payload,
            timeout=TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
                print(f"  ✅ PASSED - Found {len(tools)} tools")
                return tools
            else:
                print(f"  ❌ FAILED - Invalid response format")
                return None
        else:
            print(f"  ❌ FAILED - Status: {resp.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ FAILED - Error: {e}")
        return None


def test_tool(tools, tool_name, args=None):
    """Test calling a specific tool."""
    print(f"\n[TEST] Tool: {tool_name}")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args or {}
            }
        }
        resp = requests.post(
            f"{SERVER_URL}/mcp",
            json=payload,
            timeout=TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            if "result" in data:
                result = data["result"]
                is_error = result.get("isError", False)
                if not is_error:
                    print(f"  ✅ PASSED")
                    # Print first 100 chars of output
                    if "content" in result and len(result["content"]) > 0:
                        text = result["content"][0].get("text", "")
                        preview = text[:100].replace("\n", " ")
                        print(f"     Output: {preview}...")
                    return True
                else:
                    print(f"  ❌ FAILED - Tool returned error")
                    return False
            else:
                print(f"  ❌ FAILED - Invalid response")
                return False
        else:
            print(f"  ❌ FAILED - Status: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ FAILED - Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Termux MCP FastMCP - Integration Tests")
    print("=" * 60)
    
    # First, test if server is already running
    print("\nChecking if server is already running...")
    ping_works = test_ping()
    
    if not ping_works:
        print("\n⚠️  Server not running. Please start it with:")
        print("   python -m termux_mcp")
        print("   or")
        print("   termux-mcp")
        sys.exit(1)
    
    # Test MCP endpoint
    tools = test_mcp_endpoint()
    if not tools:
        print("\n❌ MCP endpoint not working. Check server logs.")
        sys.exit(1)
    
    # Check all 10 tools are present
    expected_tools = {
        "run_command", "get_battery", "get_location", "list_sms",
        "get_clipboard", "set_clipboard", "show_toast",
        "get_wifi_info", "list_contacts", "get_device_info"
    }
    actual_tools = {t["name"] for t in tools}
    
    print(f"\n[INFO] Expected tools: {len(expected_tools)}")
    print(f"[INFO] Actual tools: {len(actual_tools)}")
    
    if expected_tools != actual_tools:
        print(f"  ❌ Tool mismatch!")
        print(f"     Missing: {expected_tools - actual_tools}")
        print(f"     Extra: {actual_tools - expected_tools}")
    else:
        print("  ✅ All expected tools present")
    
    # Test a few tools (non-intrusive ones)
    results = []
    
    # Test run_command
    results.append(test_tool(tools, "run_command", {"cmd": "echo 'test'"}))
    
    # Test get_battery (if on Termux device)
    results.append(test_tool(tools, "get_battery"))
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
