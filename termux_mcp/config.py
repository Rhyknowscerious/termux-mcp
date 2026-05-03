import os

# Default port configurations:
#   - 666: Legacy termux-mcp (PRE-DECOMMISSION - deployable but not deployed)
#   - 8000: termux-mcp (active)
PORT: int = int(os.environ.get("TERMUX_MCP_PORT", 8000))
HOST: str = os.environ.get("TERMUX_MCP_HOST", "0.0.0.0")

# Legacy mode flag (set to True when running old termux-mcp)
LEGACY_MODE: bool = os.environ.get("TERMUX_MCP_LEGACY", "false").lower() == "true"

HOME: str = os.environ.get("HOME", "/data/data/com.termux/files/home")


AUTO_INPUT_INTERVAL: float = 0.5
PORT_POLL_INTERVAL: float = 0.3
AUTO_YES_COMMANDS: list[str] = [
    "pkg install",
    "pkg upgrade",
    "pkg update",
    "apt install",
    "apt upgrade",
    "apt update",
]
