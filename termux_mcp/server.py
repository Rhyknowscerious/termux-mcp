"""
Termux MCP Server - FastMCP Entry Point

This module provides the run() function that starts the FastMCP server
with HTTP transport on the configured host and port.
"""

import logging
import sys

from .config import HOST, PORT
from .mcp_server_fastmcp import mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the FastMCP server with HTTP transport."""
    logger.info("🚀 Starting TermuxMCP (FastMCP) on %s:%d", HOST, PORT)
    logger.info("📂 Working dir: %s", mcp.settings.get("working_dir", "unknown"))
    logger.info("Press Ctrl+C to stop.\n")
    
    try:
        # Run with HTTP transport
        mcp.run(
            transport="http",
            host=HOST,
            port=PORT,
            show_banner=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)
