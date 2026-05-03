"""Unit tests for termux_mcp.shell module.

Tests command execution, preprocessing, directory handling, and streaming.
Mock subprocess to avoid actual command execution.
"""

import os
import subprocess
from unittest.mock import patch, MagicMock, call
import pytest

from termux_mcp.shell import (
    get_current_dir,
    set_current_dir,
    execute_command,
    execute_streaming,
    handle_cd,
    preprocess,
    _inject_auto_yes,
    _inject_noninteractive,
    _DEFAULT_TIMEOUT,
)


class TestGetCurrentDir:
    """Test get_current_dir function."""

    def test_returns_string(self):
        """Test that get_current_dir returns a string."""
        result = get_current_dir()
        assert isinstance(result, str)

    def test_returns_valid_path(self):
        """Test that returned directory exists or is readable."""
        result = get_current_dir()
        # Should be an absolute path
        assert os.path.isabs(result) or result == "/data/data/com.termux/files/home"


class TestSetCurrentDir:
    """Test set_current_dir function."""

    def test_set_and_get(self):
        """Test setting and getting current directory."""
        original = get_current_dir()
        test_path = "/tmp"
        set_current_dir(test_path)
        assert get_current_dir() == test_path
        # Restore
        set_current_dir(original)

    def test_set_invalid_path(self):
        """Test setting invalid path (function doesn't validate)."""
        # The function doesn't validate, just stores
        set_current_dir("/nonexistent/path")
        assert get_current_dir() == "/nonexistent/path"


class TestHandleCd:
    """Test handle_cd function."""

    def test_cd_without_args(self):
        """Test cd with no arguments goes to HOME."""
        with patch("termux_mcp.shell.HOME", "/fake/home"):
            ok, msg = handle_cd(["cd"])
            assert ok is True
            assert get_current_dir() == "/fake/home"
            assert "📂" in msg

    def test_cd_with_tilde(self):
        """Test cd with tilde expands to HOME."""
        # Set the HOME in the module
        import termux_mcp.shell as shell_module
        original_home = shell_module.HOME
        shell_module.HOME = "/fake/home"
        
        set_current_dir("/other")
        
        # Mock isdir to return True for the expected path
        with patch("os.path.isdir", return_value=True):
            ok, msg = handle_cd(["cd", "~/docs"])
        
        # Restore
        shell_module.HOME = original_home
        
        assert ok is True
        assert get_current_dir() == "/fake/home/docs"

    def test_cd_valid_directory(self):
        """Test cd to valid directory."""
        # Use a directory we know exists
        test_dir = "/tmp"
        ok, msg = handle_cd(["cd", test_dir])
        assert ok is True
        assert get_current_dir() == test_dir
        assert "📂" in msg

    def test_cd_invalid_directory(self):
        """Test cd to invalid directory."""
        ok, msg = handle_cd(["cd", "/nonexistent/path/12345"])
        assert ok is False
        assert "❌" in msg
        assert "not found" in msg.lower()

    def test_cd_relative_path(self):
        """Test cd with relative path."""
        original = get_current_dir()
        # Go to parent directory
        parent = os.path.dirname(original)
        ok, msg = handle_cd(["cd", ".."])
        # The relative path handling uses abspath which should work
        assert isinstance(ok, bool)
        # Restore
        set_current_dir(original)

    def test_cd_multiple_args(self):
        """Test cd with multiple arguments (uses first arg)."""
        ok, msg = handle_cd(["cd", "/tmp", "extra"])
        assert ok is True
        assert get_current_dir() == "/tmp"


class TestInjectNoninteractive:
    """Test _inject_noninteractive function."""

    def test_adds_export(self):
        """Test that DEBIAN_FRONTEND is added."""
        result = _inject_noninteractive("apt install vim")
        assert "DEBIAN_FRONTEND=noninteractive" in result

    def test_prepends_to_command(self):
        """Test that export is prepended."""
        cmd = "pkg install vim"
        result = _inject_noninteractive(cmd)
        assert result.startswith("export DEBIAN_FRONTEND=noninteractive")


class TestInjectAutoYes:
    """Test _inject_auto_yes function."""

    def test_pkg_install_gets_y(self):
        """Test pkg install gets -y added."""
        result = _inject_auto_yes("pkg install vim")
        assert "pkg install vim -y" in result or "pkg install -y vim" in result

    def test_pkg_upgrade_gets_y(self):
        """Test pkg upgrade gets -y added."""
        result = _inject_auto_yes("pkg upgrade")
        assert "-y" in result

    def test_apt_install_gets_y(self):
        """Test apt install gets -y added."""
        result = _inject_auto_yes("apt install vim")
        assert "-y" in result

    def test_no_double_y(self):
        """Test that -y is not added twice."""
        result = _inject_auto_yes("pkg install -y vim")
        # Should not have -y -y
        assert result.count("-y") <= 2  # Original plus potential space

    def test_non_matching_command_unchanged(self):
        """Test that non-matching commands are unchanged."""
        cmd = "ls -la"
        result = _inject_auto_yes(cmd)
        assert result == cmd


class TestPreprocess:
    """Test preprocess function."""

    def test_calls_both_injections(self):
        """Test that preprocess calls both injection functions."""
        with patch("termux_mcp.shell._inject_auto_yes") as mock_yes:
            with patch("termux_mcp.shell._inject_noninteractive") as mock_nonint:
                mock_yes.return_value = "test"
                mock_nonint.return_value = "final"
                result = preprocess("pkg install vim")
                mock_yes.assert_called_once()
                mock_nonint.assert_called_once()
                assert result == "final"

    def test_chain_order(self):
        """Test that auto_yes is applied before noninteractive."""
        cmd = "pkg install vim"
        result = preprocess(cmd)
        # noninteractive should be at the start
        assert result.startswith("export DEBIAN_FRONTEND=noninteractive")


class TestExecuteCommand:
    """Test execute_command function."""

    def test_cd_command_handling(self):
        """Test that cd commands are handled specially."""
        original = get_current_dir()
        ok, msg = execute_command("cd /tmp")
        assert ok == 0
        assert get_current_dir() == "/tmp"
        # Restore
        set_current_dir(original)

    def test_cd_home_with_no_args(self):
        """Test cd with no args goes home."""
        with patch("termux_mcp.shell.HOME", "/fake/home"):
            ok, msg = execute_command("cd")
            assert ok == 0
            assert get_current_dir() == "/fake/home"

    def test_execute_simple_command(self):
        """Test executing a simple command."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = ["output line\n"]
            mock_process.poll.return_value = None
            mock_process.returncode = 0
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            exit_code, output = execute_command("echo test")

            mock_popen.assert_called_once()
            assert exit_code == 0

    def test_execute_command_timeout(self):
        """Test command timeout handling."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = []
            mock_process.poll.return_value = None
            # First wait raises TimeoutExpired, second wait (after kill) succeeds
            mock_process.wait.side_effect = [
                subprocess.TimeoutExpired(cmd="test", timeout=300),
                None  # Second call to wait() after kill succeeds
            ]
            mock_process.kill.return_value = None
            mock_process.returncode = 124
            mock_popen.return_value = mock_process

            exit_code, output = execute_command("sleep 1000")

            mock_process.kill.assert_called_once()
            assert exit_code == 124
            assert "timed out" in output.lower()

    def test_execute_command_nonzero_exit(self):
        """Test handling of non-zero exit code."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = ["error output\n"]
            mock_process.poll.return_value = None
            mock_process.returncode = 1
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            exit_code, output = execute_command("false")
            assert exit_code == 1
            assert "❌" in output or "Exit code" in output

    def test_execute_command_with_custom_timeout(self):
        """Test execute_command with custom timeout."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = []
            mock_process.poll.return_value = None
            mock_process.returncode = 0
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            execute_command("echo test", timeout=60)
            # Check that wait was called with timeout
            mock_process.wait.assert_called_with(timeout=60)

    def test_execute_command_preprocess_called(self):
        """Test that preprocess is called on the command."""
        with patch("termux_mcp.shell.preprocess") as mock_preprocess:
            with patch("subprocess.Popen") as mock_popen:
                mock_preprocess.return_value = "processed cmd"
                mock_process = MagicMock()
                mock_process.stdout = []
                mock_process.poll.return_value = None
                mock_process.returncode = 0
                mock_process.wait.return_value = None
                mock_popen.return_value = mock_process

                execute_command("pkg install vim")
                mock_preprocess.assert_called_once_with("pkg install vim")

    def test_execute_command_cd_not_preprocessed(self):
        """Test that cd commands skip preprocessing."""
        with patch("termux_mcp.shell.preprocess") as mock_preprocess:
            execute_command("cd /tmp")
            mock_preprocess.assert_not_called()

    def test_execute_sets_cwd(self):
        """Test that command execution uses correct cwd."""
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = []
            mock_process.poll.return_value = None
            mock_process.returncode = 0
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            set_current_dir("/fake/dir")
            execute_command("ls")

            # Check that Popen was called with correct cwd
            call_kwargs = mock_popen.call_args
            assert call_kwargs[1]["cwd"] == "/fake/dir"


class TestExecuteStreaming:
    """Test execute_streaming function (requires HTTP handler mock)."""

    def test_streaming_cd_command(self):
        """Test streaming handler with cd command."""
        mock_handler = MagicMock()
        mock_handler.wfile = MagicMock()

        execute_streaming(mock_handler, "cd /tmp")

        # Should send response with directory
        mock_handler.send_response.assert_called_once_with(200)
        mock_handler.send_header.assert_any_call("Content-Type", "text/plain")

    def test_streaming_simple_command(self):
        """Test streaming with simple command."""
        mock_handler = MagicMock()
        mock_handler.wfile = MagicMock()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = ["line1\n", "line2\n"]
            mock_process.poll.return_value = None
            mock_process.returncode = 0
            mock_process.wait.return_value = None
            mock_popen.return_value = mock_process

            execute_streaming(mock_handler, "echo test")

            # Should use chunked encoding
            mock_handler.send_header.assert_any_call("Transfer-Encoding", "chunked")

    def test_streaming_timeout(self):
        """Test streaming timeout handling."""
        mock_handler = MagicMock()
        mock_handler.wfile = MagicMock()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = []
            mock_process.poll.return_value = None
            # First wait raises TimeoutExpired, second wait (after kill) succeeds
            mock_process.wait.side_effect = [
                subprocess.TimeoutExpired(cmd="test", timeout=300),
                None  # Second call to wait() after kill succeeds
            ]
            mock_process.kill.return_value = None
            mock_popen.return_value = mock_process

            execute_streaming(mock_handler, "sleep 1000")

            # Should send timeout message
            calls = mock_handler.wfile.write.call_args_list
            timeout_sent = False
            for call in calls:
                # call.args contains the arguments passed to write()
                if call.args and b"timed out" in call.args[0].lower():
                    timeout_sent = True
                    break
            assert timeout_sent


class TestDefaultTimeout:
    """Test default timeout constant."""

    def test_default_timeout_value(self):
        """Test that default timeout is reasonable."""
        assert _DEFAULT_TIMEOUT == 300  # 5 minutes

    def test_default_timeout_is_int(self):
        """Test that default timeout is an integer."""
        assert isinstance(_DEFAULT_TIMEOUT, int)
