"""Unit tests for termux_mcp.config module.

Tests configuration loading, environment variable handling, and default values.
"""

import os
from unittest.mock import patch

import pytest

from termux_mcp.config import (
    PORT,
    HOST,
    LEGACY_MODE,
    HOME,
    AUTO_INPUT_INTERVAL,
    PORT_POLL_INTERVAL,
    AUTO_YES_COMMANDS,
)


class TestConfigDefaults:
    """Test default configuration values when no env vars are set."""

    def test_default_port(self):
        """Test default PORT is 8000."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove TERMUX_MCP_PORT if present
            env = os.environ.copy()
            env.pop("TERMUX_MCP_PORT", None)
            with patch.dict(os.environ, env, clear=True):
                # Need to reimport to get defaults
                import importlib
                from termux_mcp import config
                importlib.reload(config)
                assert config.PORT == 8000

    def test_default_host(self):
        """Test default HOST is 0.0.0.0."""
        assert HOST == "0.0.0.0"

    def test_default_legacy_mode(self):
        """Test default LEGACY_MODE is False."""
        assert LEGACY_MODE is False

    def test_default_home(self):
        """Test default HOME falls back to /data/data/com.termux/files/home."""
        with patch.dict(os.environ, {}, clear=False):
            env = os.environ.copy()
            env.pop("HOME", None)
            with patch.dict(os.environ, env, clear=True):
                import importlib
                from termux_mcp import config
                importlib.reload(config)
                assert config.HOME == "/data/data/com.termux/files/home"

    def test_default_auto_input_interval(self):
        """Test default AUTO_INPUT_INTERVAL."""
        assert AUTO_INPUT_INTERVAL == 0.5

    def test_default_port_poll_interval(self):
        """Test default PORT_POLL_INTERVAL."""
        assert PORT_POLL_INTERVAL == 0.3

    def test_default_auto_yes_commands(self):
        """Test default AUTO_YES_COMMANDS list."""
        assert isinstance(AUTO_YES_COMMANDS, list)
        assert "pkg install" in AUTO_YES_COMMANDS
        assert "pkg upgrade" in AUTO_YES_COMMANDS
        assert "apt install" in AUTO_YES_COMMANDS


class TestConfigEnvOverrides:
    """Test configuration overrides via environment variables."""

    def test_port_env_override(self):
        """Test TERMUX_MCP_PORT environment variable."""
        with patch.dict(os.environ, {"TERMUX_MCP_PORT": "9000"}):
            import importlib
            from termux_mcp import config
            importlib.reload(config)
            assert config.PORT == 9000

    def test_port_env_invalid_value(self):
        """Test TERMUX_MCP_PORT with invalid value."""
        with patch.dict(os.environ, {"TERMUX_MCP_PORT": "invalid"}):
            import importlib
            from termux_mcp import config
            # Should raise ValueError on int conversion at import time
            with pytest.raises(ValueError):
                importlib.reload(config)

    def test_host_env_override(self):
        """Test TERMUX_MCP_HOST environment variable."""
        with patch.dict(os.environ, {"TERMUX_MCP_HOST": "127.0.0.1"}):
            import importlib
            from termux_mcp import config
            importlib.reload(config)
            assert config.HOST == "127.0.0.1"

    def test_legacy_mode_env_true(self):
        """Test TERMUX_MCP_LEGACY environment variable set to true."""
        with patch.dict(os.environ, {"TERMUX_MCP_LEGACY": "true"}):
            import importlib
            from termux_mcp import config
            importlib.reload(config)
            assert config.LEGACY_MODE is True

    def test_legacy_mode_env_false(self):
        """Test TERMUX_MCP_LEGACY environment variable set to false."""
        with patch.dict(os.environ, {"TERMUX_MCP_LEGACY": "false"}):
            import importlib
            from termux_mcp import config
            importlib.reload(config)
            assert config.LEGACY_MODE is False

    def test_legacy_mode_env_case_insensitive(self):
        """Test TERMUX_MCP_LEGACY is case insensitive."""
        with patch.dict(os.environ, {"TERMUX_MCP_LEGACY": "TRUE"}):
            import importlib
            from termux_mcp import config
            importlib.reload(config)
            assert config.LEGACY_MODE is True

    def test_home_env_override(self):
        """Test HOME environment variable."""
        with patch.dict(os.environ, {"HOME": "/custom/home"}):
            import importlib
            from termux_mcp import config
            importlib.reload(config)
            assert config.HOME == "/custom/home"


class TestConfigTypes:
    """Test configuration value types."""

    def test_port_is_int(self):
        """Test PORT is an integer."""
        assert isinstance(PORT, int)

    def test_host_is_string(self):
        """Test HOST is a string."""
        assert isinstance(HOST, str)

    def test_legacy_mode_is_bool(self):
        """Test LEGACY_MODE is a boolean."""
        assert isinstance(LEGACY_MODE, bool)

    def test_auto_yes_commands_is_list(self):
        """Test AUTO_YES_COMMANDS is a list."""
        assert isinstance(AUTO_YES_COMMANDS, list)
        for cmd in AUTO_YES_COMMANDS:
            assert isinstance(cmd, str)
