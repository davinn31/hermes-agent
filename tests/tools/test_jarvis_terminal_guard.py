"""Tests for Jarvis Personal Layer terminal hard-deny guard.

Verifies that destructive terminal commands (rm -rf, git clean, git reset --hard,
etc.) are blocked when Jarvis is enabled, and that non-destructive commands and
disabled-Jarvis behavior are unaffected.
"""

import contextlib
import re

import pytest

from tools.terminal_tool_guards import (
    _JVIS_DD,
    _JVIS_GIT_CLEAN,
    _JVIS_GIT_RESET_HARD,
    _JVIS_RMDIR,
    _JVIS_RM_DESTRUCTIVE,
    _JVIS_SHRED,
    _JVIS_UNLINK,
    jarvis_terminal_block,
)

# ── Regex pattern tests ─────────────────────────────────────────────────────


class TestJarvisTerminalDetectionRegex:
    """Each destructive pattern must match real destructive commands and reject
    benign ones (quoted prose, --help, development commands, filenames that look
    like commands)."""

    @pytest.mark.parametrize("command,expected_match", [
        # rm -rf / rm -r / rm -f / rm --recursive / rm --force
        ("rm -rf /", True),
        ("rm -r build/", True),
        ("rm -f build/temp.o", True),
        ("rm --recursive /tmp/foo", True),
        ("rm --force build/temp.o", True),
        ("sudo rm -rf /tmp/foo", True),
        ("env FOO=bar rm -rf /tmp/foo", True),
        # rm WITHOUT recursive or force → not destructive under this policy
        ("rm readme.txt", False),
        ("rm foo.c", False),
        # quoted prose must not match
        ('echo "rm -rf /"', False),
        ("git commit -m 'rm -rf'", False),
        ("echo rm -rf /", False),
        # rm as part of another word → not match
        ("remark --help", False),
        (" alarm", False),
    ])
    def test_jarvis_rm_destructive_detection(self, command, expected_match):
        m = _JVIS_RM_DESTRUCTIVE.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"

    @pytest.mark.parametrize("command,expected_match", [
        ("rmdir -r build/", True),
        ("rmdir --recursive build/", True),
        ("rmdir -p a/b/c", True),
        ("rmdir build/", False),  # rmdir without -r/-p is not destructive
        ("rmdir --help", False),
        ("rmdir --version", False),
        ("echo rmdir -r /", False),  # quoted
    ])
    def test_jarvis_rmdir_detection(self, command, expected_match):
        m = _JVIS_RMDIR.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"

    @pytest.mark.parametrize("command,expected_match", [
        ("unlink file.txt", True),
        ("unlink --help", False),
        ("unlink --version", False),
        ("echo unlink file.txt", False),  # quoted
    ])
    def test_jarvis_unlink_detection(self, command, expected_match):
        m = _JVIS_UNLINK.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"

    @pytest.mark.parametrize("command,expected_match", [
        ("shred -u file.txt", True),
        ("shred file.txt", True),
        ("shred --help", False),
        ("shred --version", False),
        ("echo shred file.txt", False),
    ])
    def test_jarvis_shred_detection(self, command, expected_match):
        m = _JVIS_SHRED.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"

    @pytest.mark.parametrize("command,expected_match", [
        ("dd if=/dev/zero of=/dev/sda", True),
        ("dd of=/dev/sdb", True),
        ("dd if=/dev/zero of=image.iso", False),  # writing to file, not block device
        ("dd --help", False),
        ("echo dd if=/dev/zero of=/dev/sda", False),
    ])
    def test_jarvis_dd_detection(self, command, expected_match):
        m = _JVIS_DD.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"

    @pytest.mark.parametrize("command,expected_match", [
        ("git clean -f", True),
        ("git clean -fd", True),
        ("git clean --force", True),
        ("git clean -f -d", True),
        ("git clean", False),  # without -f/--force, not destructive
        ("git clean --help", False),
        ("echo git clean -f", False),
    ])
    def test_jarvis_git_clean_detection(self, command, expected_match):
        m = _JVIS_GIT_CLEAN.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"

    @pytest.mark.parametrize("command,expected_match", [
        ("git reset --hard", True),
        ("git reset --hard HEAD~1", True),
        ("git reset --soft HEAD~1", False),  # --soft is not destructive
        ("git reset --mixed HEAD~1", False),  # --mixed is not destructive
        ("git reset HEAD~1", False),  # default is --mixed
        ("git reset --help", False),
        ("echo git reset --hard", False),
    ])
    def test_jarvis_git_reset_hard_detection(self, command, expected_match):
        m = _JVIS_GIT_RESET_HARD.search(command)
        assert bool(m) == expected_match, f"{command!r}: expected {expected_match}, got {bool(m)}"


# ── Function behavioral tests ────────────────────────────────────────────────


@contextlib.contextmanager
def _make_controller_with_jarvis(section=None):
    """Helper: patch get_jarvis_section to return controlled config."""
    from hermes_cli import jarvis_config as jc
    orig = jc.get_jarvis_section
    jc.get_jarvis_section = lambda: section if section is not None else {"enabled": False}
    try:
        yield
    finally:
        jc.get_jarvis_section = orig


class TestJarvisTerminalBlockBehavior:
    """jarvis_terminal_block returns a block JSON when Jarvis is enabled and the
    command is destructive. When Jarvis is disabled, it returns None and Hermes
    behavior is unchanged."""

    def test_disabled_jarvis_returns_none_for_destructive_command(self):
        with _make_controller_with_jarvis({"enabled": False}):
            result = jarvis_terminal_block("rm -rf /")
            assert result is None

    def test_disabled_jarvis_returns_none_for_non_destructive_command(self):
        with _make_controller_with_jarvis({"enabled": False}):
            result = jarvis_terminal_block("echo hello")
            assert result is None

    def test_enabled_jarvis_blocks_rm_rf(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("rm -rf /tmp/foo")
            assert result is not None
            assert "blocked" in result.lower() or '"blocked"' in result

    def test_enabled_jarvis_blocks_git_clean(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("git clean -fd")
            assert result is not None

    def test_enabled_jarvis_blocks_git_reset_hard(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("git reset --hard")
            assert result is not None

    def test_enabled_jarvis_allows_non_destructive_command(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("echo hello")
            assert result is None

    def test_enabled_jarvis_allows_development_git_reset_soft(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("git reset --soft HEAD~1")
            assert result is None

    def test_enabled_jarvis_allows_git_reset_mixed(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("git reset --mixed HEAD~1")
            assert result is None

    def test_enabled_jarvis_allows_rm_without_recursive_or_force(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("rm readme.txt")
            assert result is None

    def test_enabled_jarvis_allows_rmdir_without_recursive(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("rmdir build/")
            assert result is None

    def test_enabled_jarvis_blocks_shred(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("shred -u secret.txt")
            assert result is not None

    def test_enabled_jarvis_blocks_unlink(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("unlink file.txt")
            assert result is not None

    def test_enabled_jarvis_blocks_dd_of_dev(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("dd if=/dev/zero of=/dev/sda")
            assert result is not None

    def test_enabled_jarvis_allows_dd_to_file(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("dd if=/dev/zero of=image.iso")
            assert result is None

    def test_enabled_jarvis_blocks_quoted_destructive_via_cmdpos(self):
        """quoted prose like echo 'rm -rf /' must NOT be blocked — the regex is
        command-position-anchored."""
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block('echo "rm -rf /tmp/foo"')
            assert result is None

    def test_enabled_jarvis_blocks_git_clean_force(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("git clean -f -d")
            assert result is not None

    def test_enabled_jarvis_skips_when_jarvis_import_fails(self):
        """If jarvis.security cannot be imported, the function returns None
        (backward-compatible)."""
        import sys
        orig_modules = dict(sys.modules)
        sys.modules["jarvis.security"] = None
        try:
            result = jarvis_terminal_block("rm -rf /")
            assert result is None
        finally:
            sys.modules.clear()
            sys.modules.update(orig_modules)

    def test_enabled_jarvis_skips_when_config_section_missing(self):
        """If get_jarvis_section returns a section without 'enabled' key,
        treat as disabled."""
        with _make_controller_with_jarvis({"something_else": True}):
            result = jarvis_terminal_block("rm -rf /")
            assert result is None

    def test_enabled_jarvis_skips_when_policy_is_ask(self):
        """If TERMINAL_POLICY has destructive: ASK instead of DENY, the function
        returns None (no hard block) — ASK cases fall through to the Hermes
        approval flow. This is the forward-compatible ASK handling."""
        from hermes_cli import jarvis_config as jc
        import jarvis.security as js

        orig_section = jc.get_jarvis_section
        orig_policy = js.TERMINAL_POLICY

        jc.get_jarvis_section = lambda: {"enabled": True}
        js.TERMINAL_POLICY = {"destructive": "ASK"}

        try:
            result = jarvis_terminal_block("rm -rf /")
            # ASK is not DENY, so no hard block — falls to Hermes approval
            assert result is None
        finally:
            jc.get_jarvis_section = orig_section
            js.TERMINAL_POLICY = orig_policy

    def test_non_terminal_tools_unaffected_by_jarvis_terminal_block(self):
        """jarvis_terminal_block is only called for terminal tool; other tools
        are not affected by this function (by design)."""
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("rm -rf /")
            assert result is not None  # destructive is blocked
            result2 = jarvis_terminal_block("echo hi")
            assert result2 is None  # non-destructive passes


# ── Task #11 — Terminal edge cases and policy integration tests ────────────────


class TestJarvisTerminalEdgeCases:
    """Edge cases for terminal destructive command detection that aren't covered
    by the parametrized regex tests."""

    def test_empty_command_not_blocked(self):
        """Empty string must not match any destructive pattern."""
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("")
            assert result is None

    def test_whitespace_only_command_not_blocked(self):
        """Whitespace-only commands must not be blocked."""
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in ("   ", "\t", "\n", "  \t  "):
                result = jarvis_terminal_block(cmd)
                assert result is None, f"Whitespace command {cmd!r} should not be blocked"

    def test_sudo_prefix_still_blocked(self):
        """Destructive commands with sudo prefix are still blocked."""
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in (
                "sudo rm -rf /",
                "sudo shred -u secret.txt",
                "sudo git clean -fd",
                "sudo git reset --hard",
                "sudo unlink file.txt",
                "sudo dd if=/dev/zero of=/dev/sda",
                "sudo rmdir -r build/",
            ):
                result = jarvis_terminal_block(cmd)
                assert result is not None, f"sudo {cmd} should be blocked"

    def test_all_seven_destructive_commands_blocked_in_one_sweep(self):
        """All seven required destructive commands must be blocked when Jarvis enabled."""
        with _make_controller_with_jarvis({"enabled": True}):
            destructive_commands = [
                "rm -rf /tmp/foo",
                "rmdir -r build/",
                "unlink file.txt",
                "shred -u secret.txt",
                "dd if=/dev/zero of=/dev/sda",
                "git clean -fd",
                "git reset --hard",
            ]
            for cmd in destructive_commands:
                result = jarvis_terminal_block(cmd)
                assert result is not None, f"Command {cmd!r} should be blocked"
                assert '"blocked"' in result or "blocked" in result.lower(), (
                    f"Block result for {cmd!r} should contain 'blocked' status"
                )

    def test_all_seven_destructive_commands_allowed_when_disabled(self):
        """All seven destructive commands pass through when Jarvis is disabled."""
        with _make_controller_with_jarvis({"enabled": False}):
            destructive_commands = [
                "rm -rf /tmp/foo",
                "rmdir -r build/",
                "unlink file.txt",
                "shred -u secret.txt",
                "dd if=/dev/zero of=/dev/sda",
                "git clean -fd",
                "git reset --hard",
            ]
            for cmd in destructive_commands:
                result = jarvis_terminal_block(cmd)
                assert result is None, f"Command {cmd!r} should pass when Jarvis disabled"


# ── Integration: terminal tool pre_exec_block wiring ─────────────────────────


class TestJarvisTerminalBlockInPreExecFlow:
    """Verify that _pre_exec_block in terminal_tool.py actually calls
    jarvis_terminal_block and raises _Rejected for destructive commands
    when Jarvis is enabled."""

    def test_pre_exec_blocks_destructive_when_jarvis_enabled(self):
        from tools.terminal_tool_guards import jarvis_terminal_block
        from hermes_cli import jarvis_config as jc

        orig = jc.get_jarvis_section
        jc.get_jarvis_section = lambda: {"enabled": True}
        try:
            result = jarvis_terminal_block("rm -rf /tmp/foo")
            assert result is not None
            assert "blocked" in result.lower()
        finally:
            jc.get_jarvis_section = orig

    def test_pre_exec_allows_non_destructive_when_jarvis_enabled(self):
        from tools.terminal_tool_guards import jarvis_terminal_block
        from hermes_cli import jarvis_config as jc

        orig = jc.get_jarvis_section
        jc.get_jarvis_section = lambda: {"enabled": True}
        try:
            result = jarvis_terminal_block("git status")
            assert result is None
        finally:
            jc.get_jarvis_section = orig

    def test_pre_exec_allows_when_jarvis_disabled(self):
        from tools.terminal_tool_guards import jarvis_terminal_block
        from hermes_cli import jarvis_config as jc

        orig = jc.get_jarvis_section
        jc.get_jarvis_section = lambda: {"enabled": False}
        try:
            result = jarvis_terminal_block("rm -rf /tmp/foo")
            assert result is None
        finally:
            jc.get_jarvis_section = orig


# ── Task #21A — Secret exposure enforcement tests ─────────────────────────────


class TestJarvisTerminalSecretExposure:
    """Verify that secret exposure commands are blocked when Jarvis is enabled
    and the secret_exposure policy is DENY."""

    def test_enabled_jarvis_blocks_cat_ssh_key(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("cat ~/.ssh/id_rsa")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_cat_hermes_env(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("cat ~/.hermes/.env")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_cat_project_env(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("cat .env")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_cat_credential_files(self):
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in (
                "cat ~/.netrc",
                "cat ~/.npmrc",
                "cat ~/.pypirc",
                "cat ~/.pgpass",
            ):
                result = jarvis_terminal_block(cmd)
                assert result is not None, f"{cmd} should be blocked"
                assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_cat_shell_rc(self):
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in (
                "cat ~/.bashrc",
                "cat ~/.zshrc",
                "cat ~/.profile",
            ):
                result = jarvis_terminal_block(cmd)
                assert result is not None, f"{cmd} should be blocked"
                assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_ls_ssh_key(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("ls ~/.ssh/")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_grep_in_env(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("grep API_KEY .env")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_vim_ssh_config(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("vim ~/.ssh/config")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_redirect_to_env(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("echo 'API_KEY=xyz' > .env")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_redirect_to_ssh(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("echo 'key' > ~/.ssh/authorized_keys")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_blocks_cp_to_ssh(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("cp evil_key ~/.ssh/id_rsa")
            assert result is not None
            assert "blocked" in result.lower()

    def test_enabled_jarvis_allows_normal_dev_commands(self):
        """Normal development commands that don't access sensitive paths must pass."""
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in (
                "git status",
                "git diff",
                "npm run build",
                "ls src/",
                "cat README.md",
                "grep foo bar.txt",
                "python train.py",
            ):
                result = jarvis_terminal_block(cmd)
                assert result is None, f"Command {cmd!r} should pass"

    def test_enabled_jarvis_allows_reading_non_sensitive_files(self):
        """Reading non-sensitive files must not be blocked."""
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in (
                "cat package.json",
                "cat config.json",
                "cat src/main.py",
                "ls build/",
                "head -n 10 data.csv",
            ):
                result = jarvis_terminal_block(cmd)
                assert result is None, f"Command {cmd!r} should pass"

    def test_enabled_jarvis_allows_quoted_secret_path(self):
        """Quoted prose mentioning secret paths must not be blocked."""
        with _make_controller_with_jarvis({"enabled": True}):
            for cmd in (
                'echo "cat ~/.ssh/id_rsa"',
                'git commit -m "fix: update ~/.bashrc"',
                'echo "read .env"',
            ):
                result = jarvis_terminal_block(cmd)
                assert result is None, f"Quoted prose {cmd!r} should pass"

    def test_secret_exposure_blocked_when_jarvis_disabled(self):
        """Secret exposure commands pass when Jarvis is disabled."""
        with _make_controller_with_jarvis({"enabled": False}):
            for cmd in (
                "cat ~/.ssh/id_rsa",
                "cat .env",
                "cat ~/.netrc",
            ):
                result = jarvis_terminal_block(cmd)
                assert result is None, f"Command {cmd!r} should pass when Jarvis disabled"


# ── Task #21A — Installation ASK tests (approval_detection integration) ───────


class TestJarvisTerminalInstallationAsk:
    """Verify that installation commands are NOT hard-blocked by jarvis_terminal_block
    (they return None to fall through to Hermes approval flow where they become ASK)."""

    def test_npm_install_not_hard_blocked(self):
        """npm install should return None (falls to approval flow for ASK)."""
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("npm install express")
            assert result is None, "npm install should not be hard-blocked; falls to ASK"

    def test_pnpm_install_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("pnpm install")
            assert result is None

    def test_yarn_add_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("yarn add lodash")
            assert result is None

    def test_pip_install_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("pip install requests")
            assert result is None

    def test_bun_install_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("bun install")
            assert result is None

    def test_cargo_install_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("cargo install ripgrep")
            assert result is None

    def test_go_get_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("go get github.com/foo/bar")
            assert result is None

    def test_apt_install_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("apt-get install vim")
            assert result is None

    def test_brew_install_not_hard_blocked(self):
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block("brew install git")
            assert result is None

    def test_quoted_install_not_hard_blocked(self):
        """Quoted prose like `echo "npm install"` must not be hard-blocked."""
        with _make_controller_with_jarvis({"enabled": True}):
            result = jarvis_terminal_block('echo "npm install express"')
            assert result is None
