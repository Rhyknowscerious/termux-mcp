"""
Termux MCP Server - FastMCP Implementation

This module implements the Termux MCP server using the fastmcp library.
It provides 10 tools for interacting with Termux on Android devices.
"""

import logging
import shlex
from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP, Context
from .shell import execute_command, get_current_dir

logger = logging.getLogger(__name__)

# Create the FastMCP server instance
mcp = FastMCP(
    name="termux-mcp",
    version="2.0.0",
    instructions="""
    TermuxMCP provides tools to interact with a Termux environment on Android.
    Use run_command to execute shell commands, and specialized tools for common
    Termux operations like getting battery status, location, SMS, clipboard, etc.
    """.strip()
)


@mcp.tool()
async def run_command(
    ctx: Context,
    cmd: Annotated[str, Field(description="The shell command to execute")],
    timeout: Annotated[int, Field(description="Timeout in seconds (default: 30)", default=30)] = 30
) -> str:
    """
    Execute a shell command on the Termux device.
    
    This tool runs any shell command in the Termux environment and returns
    the output. Commands run with a persistent working directory that can
    be changed using 'cd' commands.
    
    Args:
        cmd: The shell command to execute
        timeout: Timeout in seconds (default: 30)
        
    Returns:
        The command output as text
    """
    if not cmd:
        return "Error: No command provided"
    
    await ctx.info(f"Executing command: {cmd}")
    exit_code, output = execute_command(cmd, timeout=timeout)
    
    if exit_code != 0:
        await ctx.warning(f"Command exited with code {exit_code}")
    
    return output


@mcp.tool()
async def get_battery(ctx: Context) -> str:
    """
    Get battery status using termux-battery-status.
    
    Returns JSON-formatted battery information including level, status,
    temperature, and other battery metrics.
    
    Returns:
        Battery status as JSON text
    """
    await ctx.info("Getting battery status")
    exit_code, output = execute_command("termux-battery-status")
    
    if exit_code != 0:
        await ctx.error("Failed to get battery status")
    
    return output


@mcp.tool()
async def get_location(
    ctx: Context,
    provider: Annotated[str, Field(description="Location provider: gps, network, or passive", default="gps")] = "gps"
) -> str:
    """
    Get GPS location using termux-location.
    
    Retrieves the device's current location using the specified provider.
    Returns JSON with latitude, longitude, accuracy, and other location data.
    
    Args:
        provider: Location provider (gps, network, passive)
        
    Returns:
        Location data as JSON text
    """
    await ctx.info(f"Getting location using provider: {provider}")
    exit_code, output = execute_command(f"termux-location -p {shlex.quote(provider)}")
    
    if exit_code != 0:
        await ctx.error("Failed to get location")
    
    return output


@mcp.tool()
async def list_sms(
    ctx: Context,
    limit: Annotated[int, Field(description="Maximum number of messages to return", default=10)] = 10
) -> str:
    """
    List SMS messages using termux-sms-list.
    
    Retrieves SMS messages from the device with the specified limit.
    Returns JSON array of SMS messages.
    
    Args:
        limit: Maximum number of messages to return (default: 10)
        
    Returns:
        SMS messages as JSON text
    """
    await ctx.info(f"Listing SMS messages (limit: {limit})")
    exit_code, output = execute_command(f"termux-sms-list -l {shlex.quote(str(limit))}")
    
    if exit_code != 0:
        await ctx.error("Failed to list SMS messages")
    
    return output


@mcp.tool()
async def get_clipboard(ctx: Context) -> str:
    """
    Get clipboard content using termux-clipboard-get.
    
    Returns the current content of the system clipboard.
    
    Returns:
        Clipboard content as text
    """
    await ctx.info("Getting clipboard content")
    exit_code, output = execute_command("termux-clipboard-get")
    
    if exit_code != 0:
        await ctx.error("Failed to get clipboard content")
    
    return output


@mcp.tool()
async def set_clipboard(
    ctx: Context,
    text: Annotated[str, Field(description="Text to copy to clipboard")]
) -> str:
    """
    Set clipboard content using termux-clipboard-set.
    
    Copies the provided text to the system clipboard.
    
    Args:
        text: Text to copy to clipboard
        
    Returns:
        Success message or error
    """
    await ctx.info("Setting clipboard content")
    exit_code, output = execute_command(f"termux-clipboard-set {shlex.quote(text)}")
    
    if exit_code != 0:
        await ctx.error("Failed to set clipboard content")
        return output
    
    return output or "Clipboard set successfully"


@mcp.tool()
async def show_toast(
    ctx: Context,
    message: Annotated[str, Field(description="Message to display in toast")]
) -> str:
    """
    Show a toast notification using termux-toast.
    
    Displays a brief popup notification on the device screen.
    
    Args:
        message: Message to display in toast
        
    Returns:
        Success message or error
    """
    await ctx.info(f"Showing toast: {message[:50]}...")
    exit_code, output = execute_command(f"termux-toast {shlex.quote(message)}")
    
    if exit_code != 0:
        await ctx.error("Failed to show toast")
        return output
    
    return output or "Toast shown"


@mcp.tool()
async def get_wifi_info(ctx: Context) -> str:
    """
    Get WiFi connection info using termux-wifi-connectioninfo.
    
    Returns JSON-formatted WiFi connection information including
    SSID, IP address, link speed, and signal strength.
    
    Returns:
        WiFi info as JSON text
    """
    await ctx.info("Getting WiFi info")
    exit_code, output = execute_command("termux-wifi-connectioninfo")
    
    if exit_code != 0:
        await ctx.error("Failed to get WiFi info")
    
    return output


@mcp.tool()
async def list_contacts(ctx: Context) -> str:
    """
    List contacts using termux-contact-list.
    
    Returns JSON array of contacts from the device's contact list.
    
    Returns:
        Contacts as JSON text
    """
    await ctx.info("Listing contacts")
    exit_code, output = execute_command("termux-contact-list")
    
    if exit_code != 0:
        await ctx.error("Failed to list contacts")
    
    return output


@mcp.tool()
async def get_device_info(ctx: Context) -> str:
    """
    Get device info using termux-info.
    
    Returns information about the Termux environment and device,
    including package lists, system info, and environment variables.
    
    Returns:
        Device info as text
    """
    await ctx.info("Getting device info")
    exit_code, output = execute_command("termux-info")
    
    if exit_code != 0:
        await ctx.error("Failed to get device info")
    
    return output


# Export the mcp instance for use in server.py
__all__ = ['mcp']
