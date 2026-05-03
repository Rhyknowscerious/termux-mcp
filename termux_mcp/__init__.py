__version__ = "2.0.0"
__author__ = "Parixit Sutariya, ry4n"

# Export the FastMCP server instance for direct access
from .mcp_server_fastmcp import mcp

__all__ = ["mcp", "run"]

# Export remote client components for easy access (if available)
try:
    from .remote_client import (
        TermuxDeviceConfig,
        RemoteTermuxClient,
        CommandResult,
        DeviceManager,
        ConnectionMode,
        execute_remote_command,
        call_remote_tool,
        FastMCPCompatClient,
        device_manager,
    )
    __all__.extend([
        "TermuxDeviceConfig",
        "RemoteTermuxClient",
        "CommandResult",
        "DeviceManager",
        "ConnectionMode",
        "execute_remote_command",
        "call_remote_tool",
        "FastMCPCompatClient",
        "device_manager",
    ])
except ImportError:
    # remote_client.py not available
    pass
