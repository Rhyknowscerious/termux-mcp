"""Unit tests for termux_mcp.security module.

Tests command risk assessment, dangerous command detection, and pattern matching.
"""

import pytest

from termux_mcp.security import (
    CommandRiskLevel,
    DANGEROUS_PATTERNS,
    WARNING_PATTERNS,
    is_dangerous_command,
    get_risk_assessment,
)


class TestCommandRiskLevel:
    """Test CommandRiskLevel constants."""

    def test_safe_level(self):
        """Test SAFE risk level constant."""
        assert CommandRiskLevel.SAFE == "safe"

    def test_warning_level(self):
        """Test WARNING risk level constant."""
        assert CommandRiskLevel.WARNING == "warning"

    def test_dangerous_level(self):
        """Test DANGEROUS risk level constant."""
        assert CommandRiskLevel.DANGEROUS == "dangerous"


class TestDangerousCommandDetection:
    """Test detection of dangerous commands."""

    def test_rm_rf_root(self):
        """Test detection of 'rm -rf /'."""
        blocked, level, msg = is_dangerous_command("rm -rf /")
        assert blocked is True
        assert level == CommandRiskLevel.DANGEROUS

    def test_rm_rf_root_with_tabs(self):
        """Test detection of 'rm -rf /' with tabs."""
        blocked, level, msg = is_dangerous_command("rm -rf\t/")
        assert blocked is True

    def test_rm_rf_home(self):
        """Test detection of 'rm -rf ~'."""
        blocked, level, msg = is_dangerous_command("rm -rf ~")
        assert blocked is True
        assert level == CommandRiskLevel.DANGEROUS

    def test_rm_rf_wildcard_root(self):
        """Test detection of 'rm -rf /*'."""
        blocked, level, msg = is_dangerous_command("rm -rf /*")
        assert blocked is True

    def test_rm_rf_no_preserve_root(self):
        """Test detection of rm with --no-preserve-root."""
        blocked, level, msg = is_dangerous_command("rm -rf --no-preserve-root /")
        assert blocked is True

    def test_dd_command(self):
        """Test detection of dd command."""
        blocked, level, msg = is_dangerous_command("dd if=/dev/zero of=/dev/sda")
        assert blocked is True
        assert level == CommandRiskLevel.DANGEROUS

    def test_mkfs_command(self):
        """Test detection of mkfs command."""
        blocked, level, msg = is_dangerous_command("mkfs.ext4 /dev/sda")
        assert blocked is True

    def test_fork_bomb(self):
        """Test detection of fork bomb."""
        blocked, level, msg = is_dangerous_command(":(){ :|:& };:")
        assert blocked is True

    def test_redirect_to_dev(self):
        """Test detection of redirect to /dev."""
        blocked, level, msg = is_dangerous_command("echo test > /dev/sda")
        assert blocked is True

    def test_chmod_777_recursive(self):
        """Test detection of chmod -R 777."""
        blocked, level, msg = is_dangerous_command("chmod -R 777 /")
        assert blocked is True

    def test_chmod_000_recursive(self):
        """Test detection of chmod -R 000."""
        blocked, level, msg = is_dangerous_command("chmod -R 000 /home")
        assert blocked is True

    def test_chown_root_recursive(self):
        """Test detection of chown -R root."""
        blocked, level, msg = is_dangerous_command("chown -R root /")
        assert blocked is True

    def test_pkg_remove_termux(self):
        """Test detection of pkg remove termux."""
        blocked, level, msg = is_dangerous_command("pkg remove termux-api")
        assert blocked is True

    def test_apt_purge_termux(self):
        """Test detection of apt purge termux packages."""
        blocked, level, msg = is_dangerous_command("apt purge -y termux-api")
        assert blocked is True

    def test_rm_rf_after_semicolon(self):
        """Test detection of rm -rf after semicolon."""
        blocked, level, msg = is_dangerous_command("echo test; rm -rf /")
        assert blocked is True

    def test_rm_rf_after_and(self):
        """Test detection of rm -rf after &&."""
        blocked, level, msg = is_dangerous_command("cd / && rm -rf /")
        assert blocked is True

    def test_rm_rf_after_pipe(self):
        """Test detection of rm -rf after pipe."""
        blocked, level, msg = is_dangerous_command("ls | rm -rf /")
        assert blocked is True


class TestWarningCommandDetection:
    """Test detection of warning-level commands."""

    def test_rm_rf_directory(self):
        """Test detection of rm -rf on directory."""
        blocked, level, msg = is_dangerous_command("rm -rf /home/user/tmp")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_rm_r(self):
        """Test detection of rm -r."""
        blocked, level, msg = is_dangerous_command("rm -r /tmp/test")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_redirect_to_dev_null(self):
        """Test detection of redirect to /dev/null."""
        blocked, level, msg = is_dangerous_command("echo test >> /dev/null")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_chmod_recursive(self):
        """Test detection of chmod -R."""
        blocked, level, msg = is_dangerous_command("chmod -R 755 /home")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_find_delete(self):
        """Test detection of find with -delete."""
        blocked, level, msg = is_dangerous_command("find /tmp -name '*.tmp' -delete")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_redirect_to_root(self):
        """Test detection of redirect to root path."""
        blocked, level, msg = is_dangerous_command("echo test > /etc/config")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING


class TestSafeCommands:
    """Test that safe commands are not flagged."""

    def test_simple_ls(self):
        """Test 'ls' is safe."""
        blocked, level, msg = is_dangerous_command("ls")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_echo(self):
        """Test 'echo' is safe."""
        blocked, level, msg = is_dangerous_command("echo hello")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_pkg_install(self):
        """Test 'pkg install' is safe."""
        blocked, level, msg = is_dangerous_command("pkg install vim")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_cd_command(self):
        """Test 'cd' is safe."""
        blocked, level, msg = is_dangerous_command("cd /home")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_mkdir(self):
        """Test 'mkdir' is safe."""
        blocked, level, msg = is_dangerous_command("mkdir test")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_git_command(self):
        """Test 'git' commands are safe."""
        blocked, level, msg = is_dangerous_command("git status")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE


class TestSudoDetection:
    """Test sudo command detection."""

    def test_sudo_with_rm(self):
        """Test sudo with rm detection."""
        blocked, level, msg = is_dangerous_command("sudo rm -rf /tmp")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING
        assert "sudo" in msg.lower()


class TestShutdownDetection:
    """Test shutdown/reboot command detection."""

    def test_reboot(self):
        """Test reboot command detection."""
        blocked, level, msg = is_dangerous_command("reboot")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_shutdown(self):
        """Test shutdown command detection."""
        blocked, level, msg = is_dangerous_command("shutdown now")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING

    def test_poweroff(self):
        """Test poweroff command detection."""
        blocked, level, msg = is_dangerous_command("poweroff")
        assert blocked is False
        assert level == CommandRiskLevel.WARNING


class TestEmptyAndShortCommands:
    """Test handling of empty and very short commands."""

    def test_empty_command(self):
        """Test empty command handling."""
        blocked, level, msg = is_dangerous_command("")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_whitespace_only(self):
        """Test whitespace-only command."""
        blocked, level, msg = is_dangerous_command("   ")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE

    def test_very_short_command(self):
        """Test very short command (less than 3 chars)."""
        blocked, level, msg = is_dangerous_command("ls")
        assert blocked is False
        assert level == CommandRiskLevel.SAFE


class TestGetRiskAssessment:
    """Test get_risk_assessment function."""

    def test_safe_assessment(self):
        """Test risk assessment for safe command."""
        result = get_risk_assessment("ls -la")
        assert result["command"] == "ls -la"
        assert result["risk_level"] == CommandRiskLevel.SAFE
        assert result["blocked"] is False
        assert result["requires_confirmation"] is False

    def test_warning_assessment(self):
        """Test risk assessment for warning command."""
        result = get_risk_assessment("rm -rf /tmp/test")
        assert result["risk_level"] == CommandRiskLevel.WARNING
        assert result["blocked"] is False
        assert result["requires_confirmation"] is True

    def test_dangerous_assessment(self):
        """Test risk assessment for dangerous command."""
        result = get_risk_assessment("rm -rf /")
        assert result["risk_level"] == CommandRiskLevel.DANGEROUS
        assert result["blocked"] is True
        assert result["requires_confirmation"] is False

    def test_assessment_message_present(self):
        """Test that assessment includes a message."""
        result = get_risk_assessment("ls")
        assert "message" in result
        assert len(result["message"]) > 0

    def test_assessment_structure(self):
        """Test that assessment returns all expected keys."""
        result = get_risk_assessment("echo test")
        expected_keys = {"command", "risk_level", "blocked", "message", "requires_confirmation"}
        assert set(result.keys()) == expected_keys


class TestCaseInsensitiveDetection:
    """Test that detection is case insensitive."""

    def test_uppercase_rm(self):
        """Test uppercase RM command."""
        blocked, level, msg = is_dangerous_command("RM -RF /")
        assert blocked is True

    def test_mixed_case_rm(self):
        """Test mixed case Rm command."""
        blocked, level, msg = is_dangerous_command("Rm -Rf /")
        assert blocked is True

    def test_uppercase_dd(self):
        """Test uppercase DD command."""
        blocked, level, msg = is_dangerous_command("DD IF=/dev/zero OF=/dev/sda")
        assert blocked is True
