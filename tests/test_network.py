"""Unit tests for termux_mcp.network module.

Tests port killing and network utility functions.
"""

import socket
from unittest.mock import patch, MagicMock
import subprocess
import time

from termux_mcp.network import kill_port
from termux_mcp.config import PORT_POLL_INTERVAL


class TestKillPort:
    """Test kill_port function."""

    def setup_mock_socket(self, mock_socket, connect_ex_values=None):
        """Helper to set up mock socket."""
        mock_sock_instance = MagicMock()
        if connect_ex_values:
            mock_sock_instance.connect_ex.side_effect = connect_ex_values
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.__enter__ = lambda s: mock_sock_instance
        mock_sock_instance.__exit__ = MagicMock(return_value=False)
        return mock_sock_instance

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_kill_port_no_process_running(self, mock_socket, mock_run):
        """Test kill_port when no process is using the port."""
        # Simulate no process found
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        
        # Simulate port not in use
        self.setup_mock_socket(mock_socket, connect_ex_values=[1])
        
        kill_port(8000)

        # Should have called lsof
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_kill_port_with_process(self, mock_socket, mock_run):
        """Test kill_port when a process is using the port."""
        # Simulate process found (pid 1234)
        mock_run.return_value = MagicMock(stdout="1234\n", returncode=0)
        
        # Simulate port still in use after kill, then free
        self.setup_mock_socket(mock_socket, connect_ex_values=[0, 1])
        
        with patch("time.sleep") as mock_sleep:
            kill_port(8000)

        # Should have called kill -9
        kill_calls = [call for call in mock_run.call_args_list if "kill" in str(call)]
        assert len(kill_calls) > 0

    @patch("subprocess.run")
    def test_kill_port_exception_handled(self, mock_run):
        """Test that exceptions in kill_port are handled."""
        mock_run.side_effect = Exception("Test exception")
        
        # Mock socket to return that port is free (so while loop exits)
        with patch("socket.socket") as mock_socket:
            self.setup_mock_socket(mock_socket, connect_ex_values=[1])
            
            # Should not raise
            try:
                kill_port(8000)
            except Exception:
                pytest.fail("kill_port should handle exceptions gracefully")

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_kill_port_multiple_pids(self, mock_socket, mock_run):
        """Test kill_port with multiple PIDs."""
        # Simulate multiple processes
        mock_run.return_value = MagicMock(stdout="1234\n5678\n", returncode=0)
        
        self.setup_mock_socket(mock_socket, connect_ex_values=[1])
        
        kill_port(8000)

        # Should have killed both processes
        assert mock_run.call_count >= 3  # One lsof + two kills

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_kill_port_polls_until_free(self, mock_socket, mock_run):
        """Test that kill_port polls until port is free."""
        mock_run.return_value = MagicMock(stdout="1234\n", returncode=0)
        
        # Simulate port in use several times, then free
        self.setup_mock_socket(mock_socket, connect_ex_values=[0, 0, 0, 1])
        
        with patch("time.sleep") as mock_sleep:
            kill_port(8000)
            # Should have slept while waiting
            assert mock_sleep.call_count >= 2

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_kill_port_zero(self, mock_socket, mock_run):
        """Test kill_port with port 0 (edge case)."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        self.setup_mock_socket(mock_socket, connect_ex_values=[1])
        
        kill_port(0)

    @patch("subprocess.run")
    @patch("socket.socket")
    def test_kill_port_privileged(self, mock_socket, mock_run):
        """Test kill_port with privileged port."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        self.setup_mock_socket(mock_socket, connect_ex_values=[1])
        
        kill_port(80)
